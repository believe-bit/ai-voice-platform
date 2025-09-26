import os
os.environ["PYTHONUNBUFFERED"] = "1"
import sys
import subprocess
import logging
import zipfile
import shutil
from flask import Flask, render_template, request, jsonify, send_from_directory, Response, send_file
from flask_socketio import SocketIO, emit
from flask_cors import CORS  # 导入 flask_cors
import numpy as np
import time
from werkzeug.exceptions import ClientDisconnected
import warnings
import threading
import queue
import uuid

# 忽略警告
warnings.filterwarnings("ignore")
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)
logging.getLogger('socketio').setLevel(logging.ERROR)
logging.getLogger('engineio').setLevel(logging.ERROR)

# 路径配置
MODEL_ROOT = "/home/believe/AI_Voice_Platform/models/ASR_models"
TRAIN_MODEL_ROOT = "/home/believe/AI_Voice_Platform/models/ASR_train_models"
TTS_MODEL_ROOT = "/home/believe/AI_Voice_Platform/models/TTS_models"
TTS_VOICE_MODEL_ROOT = "/home/believe/AI_Voice_Platform/models/TTS_voice_models"  # 语音克隆模型路径
VITS_MODEL_ROOT = "/home/believe/AI_Voice_Platform/models/VITS_train_models"  # 新增 VITS 模型路径
SAVE_MODEL_ROOT = "/home/believe/AI_Voice_Platform/models/Save_ASR_train_models"
SAVE_AUDIO_ROOT = "/home/believe/AI_Voice_Platform/Save_audio"
SAVE_TTS_TRAIN_ROOT = "/home/believe/AI_Voice_Platform/models/Save_TTS_train"
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'Uploads')
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
if not os.path.exists(SAVE_MODEL_ROOT):
    os.makedirs(SAVE_MODEL_ROOT)
if not os.path.exists(SAVE_AUDIO_ROOT):
    os.makedirs(SAVE_AUDIO_ROOT)
if not os.path.exists(SAVE_TTS_TRAIN_ROOT):
    os.makedirs(SAVE_TTS_TRAIN_ROOT)
    

app = Flask(__name__, template_folder='templates')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
CORS(app, resources={r"/*": {"origins": "http://localhost:8080"}})  # 允许来自 localhost:8080 的请求
socketio = SocketIO(app, cors_allowed_origins="http://localhost:8080")  # 更新 SocketIO 的 CORS 配置

# 全局变量存储子进程
recognition_process = None
training_process = None
tts_process = None
tts_train_process = None
tts_test_process = None
log_queue = queue.Queue()
process_lock = threading.Lock()

vits_train_log_queue = queue.Queue()
vits_test_log_queue = queue.Queue()

# 导入语音识别API相关方法
from recognition_seq2seq import get_available_models, load_local_model, start_ws_server
# 导入模型相关方法
# 主页路由
@app.route('/')
def index():
    return render_template('index.html')

# API：列出语音识别模型（替换为 app1.py 逻辑）
@app.route('/models', methods=['GET'])
def get_models():
    models = get_available_models()
    return jsonify(models)

# API：加载语音识别模型（替换为 app1.py 逻辑）
@app.route('/load_model', methods=['POST'])
def load_model():
    data = request.get_json()
    selected_model = data.get("model")
    if not selected_model:
        return jsonify({"status": "error", "message": "未选择模型"})
    result = load_local_model(selected_model)
    return jsonify(result)

# API：列出模型
@app.route('/list_models', methods=['GET'])
def list_models():
    section = request.args.get('section', 'asr')
    try:
        if section == 'asr':
            model_dir = MODEL_ROOT
        elif section == 'asr-finetune':
            model_dir = TRAIN_MODEL_ROOT
        elif section == 'tts':
            model_dir = TTS_MODEL_ROOT
        elif section == 'vits':
            model_dir = SAVE_TTS_TRAIN_ROOT
        else:
            return jsonify({'error': '无效的 section 参数'}), 400

        models = [d for d in os.listdir(model_dir) if os.path.isdir(os.path.join(model_dir, d))]
        print(f"{section} 模型列表: {models}", file=sys.stderr)
        return jsonify(models)
    except Exception as e:
        print(f"获取 {section} 模型列表失败: {str(e)}", file=sys.stderr)
        return jsonify({'error': str(e)}), 500

# API：离线音频文件识别
@app.route('/recognize', methods=['POST'])
def recognize():
    if 'audio' not in request.files:
        return jsonify({'error': '无音频文件'})
    file = request.files['audio']
    model = request.form.get('model')
    if file.filename == '' or not model:
        return jsonify({'error': '无效输入'})

    file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    file.save(file_path)

    conda_env_name = "asr_infer_env"
    conda_activate = "/home/believe/anaconda3/bin/activate"
    if not os.path.exists(conda_activate):
        return jsonify({'error': f'Anaconda 激活脚本未找到：{conda_activate}'})

    cmd = f'. "{conda_activate}" {conda_env_name} && python recognize.py "{file_path}" "{model}"'

    try:
        result = subprocess.run(
            ["/bin/bash", "-c", cmd],
            capture_output=True,
            text=True,
            encoding='utf-8'
        )
        output = result.stdout.strip()
        error = result.stderr.strip()
        if result.returncode != 0:
            return jsonify({'error': f'子进程错误：{error}'})
        return jsonify({'text': output if output else '无识别结果'})
    except Exception as e:
        return jsonify({'error': f'子进程调用失败：{str(e)}'})

# API：上传数据集
@app.route('/upload_dataset', methods=['POST'])
def upload_dataset():
    if 'file' not in request.files:
        return jsonify({"error": "没有提供文件"}), 400
    file = request.files['file']
    if not file.filename.endswith('.zip'):
        return jsonify({"error": "文件必须是 ZIP 压缩包"}), 400

    dataset_id = str(uuid.uuid4())
    dataset_path = os.path.join(app.config['UPLOAD_FOLDER'], dataset_id)
    os.makedirs(dataset_path, exist_ok=True)

    zip_path = os.path.join(dataset_path, file.filename)
    file.save(zip_path)

    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(dataset_path)
        os.remove(zip_path)  # 解压后删除 ZIP 文件

        # 检查是否有至少一个 .wav 和对应 .trn 文件
        wav_files = []
        trn_files = []
        for root, _, files in os.walk(dataset_path):
            for f in files:
                if f.endswith('.wav'):
                    wav_files.append(os.path.join(root, f))
                elif f.endswith('.trn'):
                    trn_files.append(os.path.join(root, f))
        if not wav_files or not trn_files:
            shutil.rmtree(dataset_path, ignore_errors=True)
            return jsonify({"error": "数据集缺少 .wav 或 .trn 文件"}), 400

        # 可选：统计有效样本数
        valid_count = 0
        for wav_file in wav_files:
            trn_file = wav_file + ".trn"
            if os.path.exists(trn_file):
                with open(trn_file, "r", encoding="utf-8") as f:
                    first_line = f.readline().strip()
                    if first_line:
                        valid_count += 1

        return jsonify({"dataset_path": dataset_path, "valid_samples": valid_count})
    except Exception as e:
        shutil.rmtree(dataset_path, ignore_errors=True)
        return jsonify({"error": f"解压 ZIP 文件失败：{str(e)}"}), 500

# API：获取生成的音频
@app.route('/audio/<filename>')
def serve_audio(filename):
    audio_path = os.path.join(SAVE_AUDIO_ROOT, filename)
    print(f"请求音频文件: {audio_path}", file=sys.stderr)
    if not os.path.exists(audio_path):
        print(f"音频文件不存在: {audio_path}", file=sys.stderr)
        return {"error": f"音频文件不存在: {audio_path}"}, 404
    print(f"找到音频文件: {audio_path}, 返回文件", file=sys.stderr)
    return send_file(audio_path, mimetype='audio/wav')

# API：上传复刻音色音频
@app.route('/upload_voice_clone_audio', methods=['POST'])
def upload_voice_clone_audio():
    if 'audio' not in request.files:
        return jsonify({'error': '无音频文件'}), 400
    file = request.files['audio']
    if file.filename == '':
        return jsonify({'error': '无效输入'}), 400

    try:
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(file_path)
        return jsonify({
            'status': 'success',
            'path': file_path,
            'message': '文件上传成功'
        })
    except Exception as e:
        return jsonify({
            'error': f'文件保存失败: {str(e)}'
        }), 500

    return jsonify({'status': 'success', 'file_path': file_path})

    # 生成唯一输出文件名
    output_filename = f"clone_{int(time.time())}.wav"
    output_path = os.path.join(SAVE_AUDIO_ROOT, output_filename)

    # 调用 voice.py 执行克隆
    conda_env_name = "asr_infer_env"
    conda_activate = "/home/believe/anaconda3/bin/activate"
    cmd = (
        f'. "{conda_activate}" {conda_env_name} && '
        f'python voice.py "{model}" "{audio_path}" "{text}" "{lang_tip}" "{output_path}"'
    )

    with process_lock:
        if tts_process and tts_process.poll() is None:
            emit('voice_clone_result', {'error': '已有克隆任务在进行中'})
            return

        try:
            tts_process = subprocess.Popen(
                ["/bin/bash", "-c", cmd],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8'
            )
            emit('voice_clone_result', {'text': '克隆任务已启动'})
        except Exception as e:
            emit('voice_clone_result', {'error': f'启动克隆失败: {str(e)}'})

# API：VITS模型训练
@app.route('/vits_train', methods=['POST'])
def vits_train():
    global tts_train_process
    data = request.get_json()
    dataset_path = data.get("dataset_path")
    epochs = data.get("epochs", 20)
    batch_size = data.get("batch_size", 16)
    lr = data.get("lr", 1e-5)
    use_gpu = data.get("use_gpu", False)
    model_name = data.get("model_name", "default_model")

    if not dataset_path or not os.path.exists(dataset_path):
        return jsonify({"error": "数据集路径无效"}), 400

    model_dir = os.path.join(SAVE_TTS_TRAIN_ROOT, model_name)
    version = 1
    while os.path.exists(model_dir):
        model_dir = os.path.join(SAVE_TTS_TRAIN_ROOT, f"{model_name}_V{version}")
        version += 1

    os.makedirs(model_dir, exist_ok=True)

    conda_env_name = "voice"
    conda_activate = "/home/believe/anaconda3/bin/activate"
    if not os.path.exists(conda_activate):
        return jsonify({"error": f"Anaconda 激活脚本未找到：{conda_activate}"}), 400

    cmd = (
        f'. "{conda_activate}" {conda_env_name} && python tts_train.py '
        f'--data_dir "{dataset_path}" --epochs {epochs} --batch_size {batch_size} '
        f'--lr {lr} --device {"cuda" if use_gpu else "cpu"} --model_dir "{model_dir}"'
    )

    try:
        with process_lock:
            if tts_train_process and tts_train_process.poll() is None:
                return jsonify({"error": "已有训练进程在运行"}), 400
            tts_train_process = subprocess.Popen(
                ["/bin/bash", "-c", cmd],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8'
            )
        print(f"启动 VITS 训练: {cmd}", file=sys.stderr)
        threading.Thread(target=read_vits_train_output, args=(tts_train_process, model_dir), daemon=True).start()
        return jsonify({"status": "训练已启动", "model_dir": model_dir})
    except Exception as e:
        return jsonify({"error": f"启动训练失败：{str(e)}"}), 500

# 添加 VITS 训练日志读取
def read_vits_train_output(process, model_dir):
    while process and process.poll() is None:
        output = process.stdout.readline().strip()
        error = process.stderr.readline().strip()
        if output:
            print(f"VITS 训练输出: {output}", file=sys.stderr)
            vits_train_log_queue.put(output)
        if error:
            print(f"VITS 训练错误: {error}", file=sys.stderr)
            vits_train_log_queue.put(error)
    stdout, stderr = process.communicate()
    if stdout:
        for line in stdout.splitlines():
            line = line.strip()
            if line:
                vits_train_log_queue.put(line)
    if stderr:
        for line in stderr.splitlines():
            line = line.strip()
            if line:
                vits_train_log_queue.put(line)
    vits_train_log_queue.put("[训练完成]")


# API：停止VITS模型训练
@app.route('/vits_stop_train', methods=['POST'])
def vits_stop_train():
    with process_lock:
        global tts_train_process
        if tts_train_process:
            tts_train_process.terminate()
            tts_train_process = None
            return jsonify({"status": "训练已停止"})
        else:
            return jsonify({"error": "没有正在运行的训练进程"}), 400

# API：VITS模型测试
@app.route('/vits_test', methods=['POST'])
def vits_test():
    global tts_test_process
    data = request.get_json()
    model_name = data.get("model_name")
    text = data.get("text")
    speech_rate = data.get("speech_rate", 1.0)
    volume = data.get("volume", 1.0)

    if not model_name or not text:
        return jsonify({"error": "模型名称或文本未提供"}), 400

    model_dir = os.path.join(SAVE_TTS_TRAIN_ROOT, model_name)
    if not os.path.exists(model_dir):
        return jsonify({"error": "模型目录不存在"}), 400

    model_path = None
    tokenizer_path = None
    for root, _, files in os.walk(model_dir):
        for file in files:
            if file.endswith('.pth'):
                model_path = os.path.join(root, file)
            elif file.endswith('.pkl'):
                tokenizer_path = os.path.join(root, file)

    if not model_path or not tokenizer_path:
        return jsonify({"error": "模型文件或分词器文件缺失"}), 400

    output_filename = f"test_{uuid.uuid4().hex}.wav"
    output_path = os.path.join(SAVE_AUDIO_ROOT, output_filename)

    conda_env_name = "voice"
    conda_activate = "/home/believe/anaconda3/bin/activate"
    if not os.path.exists(conda_activate):
        return jsonify({"error": f"Anaconda 激活脚本未找到：{conda_activate}"}), 400

    cmd = (
        f'. "{conda_activate}" {conda_env_name} && python tts_test.py '
        f'--model_path "{model_path}" --tokenizer_path "{tokenizer_path}" '
        f'--text "{text}" --speech_rate {speech_rate} --volume {volume} '
        f'--output_path "{output_path}"'
    )

    try:
        with process_lock:
            if tts_test_process and tts_test_process.poll() is None:
                return jsonify({"error": "已有测试进程在运行"}), 400
            tts_test_process = subprocess.Popen(
                ["/bin/bash", "-c", cmd],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8'
            )
        print(f"启动 VITS 测试: {cmd}", file=sys.stderr)
        threading.Thread(target=read_vits_test_output, args=(tts_test_process, output_filename), daemon=True).start()
        return jsonify({"status": "测试已启动", "audio_path": output_filename})
    except Exception as e:
        return jsonify({"error": f"启动测试失败：{str(e)}"}), 500

# 添加 VITS 测试日志读取
def read_vits_test_output(process, output_filename):
    print(f"开始读取 VITS 测试输出: {output_filename}", file=sys.stderr)
    while process and process.poll() is None:
        output = process.stdout.readline().strip()
        error = process.stderr.readline().strip()
        if output:
            print(f"VITS 测试输出: {output}", file=sys.stderr)
            vits_test_log_queue.put(output)
        if error:
            print(f"VITS 测试错误: {error}", file=sys.stderr)
            vits_test_log_queue.put(error)
    stdout, stderr = process.communicate()
    if stdout:
        for line in stdout.splitlines():
            line = line.strip()
            if line:
                print(f"VITS 测试输出(剩余): {line}", file=sys.stderr)
                vits_test_log_queue.put(line)
    if stderr:
        for line in stderr.splitlines():
            line = line.strip()
            if line:
                print(f"VITS 测试错误(剩余): {line}", file=sys.stderr)
                vits_test_log_queue.put(line)
    vits_test_log_queue.put("[测试完成]")
    print(f"VITS 测试日志流结束: {output_filename}", file=sys.stderr)

# API：获取VITS模型训练日志
@app.route('/vits_train_log', methods=['GET'])
def vits_train_log_endpoint():
    def stream():
        while True:
            log = vits_train_log_queue.get()
            yield f"data: {log}\n\n"
            if log in ("[训练完成]", "[训练已停止]"):
                break
    return Response(stream(), mimetype='text/event-stream')

# API：获取VITS模型测试日志
@app.route('/vits_test_log', methods=['GET'])
def vits_test_log_endpoint():
    print("客户端连接到 /vits_test_log", file=sys.stderr)
    def stream():
        try:
            while True:
                log = vits_test_log_queue.get()
                print(f"发送测试日志: {log}", file=sys.stderr)
                yield f"data: {log}\n\n"
                if log == "[测试完成]":
                    break
        except GeneratorExit:
            print("客户端断开 /vits_test_log 连接", file=sys.stderr)
    return Response(stream(), mimetype='text/event-stream')

# WebSocket：启动实时识别子进程
@socketio.on('start_recognition_process')
def start_recognition_process(data):
    global recognition_process
    model = data.get('model')
    if not model:
        emit('recognition_result', {'error': '未选择模型'})
        print('错误：未选择模型', file=sys.stderr)
        return

    conda_env_name = "asr_infer_env"
    conda_activate = "/home/believe/anaconda3/bin/activate"
    if not os.path.exists(conda_activate):
        emit('recognition_result', {'error': f'Anaconda 激活脚本未找到：{conda_activate}'})
        print(f'错误：Anaconda 激活脚本未找到：{conda_activate}', file=sys.stderr)
        return

    cmd = f'. "{conda_activate}" {conda_env_name} && python recognition_seq2seq.py "{model}"'
    
    try:
        if recognition_process and recognition_process.poll() is None:
            emit('recognition_result', {'error': '已有正在运行的识别进程'})
            print('错误：已有正在运行的识别进程', file=sys.stderr)
            return
        recognition_process = subprocess.Popen(
            ["/bin/bash", "-c", cmd],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8'
        )
        emit('recognition_result', {'text': '实时识别子进程启动成功'})
        print(f'实时识别子进程启动成功 (PID: {recognition_process.pid})', file=sys.stderr)
        socketio.start_background_task(read_recognition_output)
    except Exception as e:
        emit('recognition_result', {'error': f'子进程启动失败：{str(e)}'})
        print(f'子进程启动失败：{str(e)}', file=sys.stderr)

# WebSocket：处理麦克风音频数据
@socketio.on('audio_data')
def handle_audio_data(data):
    global recognition_process
    if not recognition_process or recognition_process.poll() is not None:
        emit('recognition_result', {'error': '实时识别进程未运行'})
        print('错误：实时识别进程未运行', file=sys.stderr)
        return
    try:
        # 假设前端发送的是逗号分隔的浮点数字符串
        audio_str = ','.join(map(str, data))
        recognition_process.stdin.write(audio_str + '\n')
        recognition_process.stdin.flush()
        print(f'发送音频块成功，长度: {len(data)}', file=sys.stderr)
    except Exception as e:
        emit('recognition_result', {'error': f'音频处理失败：{str(e)}'})
        print(f'音频处理失败：{str(e)}', file=sys.stderr)

# WebSocket：停止实时识别
@socketio.on('stop_recognition')
def stop_recognition():
    global recognition_process
    if recognition_process and recognition_process.poll() is None:
        try:
            recognition_process.stdin.write("END\n")
            recognition_process.stdin.flush()
            recognition_process.stdin.close()
            stdout, stderr = recognition_process.communicate(timeout=2)
            if stdout:
                print(f'识别子进程最终输出: {stdout}', file=sys.stderr)
                socketio.emit('recognition_result', {'text': stdout.strip()})
            if stderr:
                print(f'识别子进程最终错误: {stderr}', file=sys.stderr)
                socketio.emit('recognition_result', {'error': stderr.strip()})
            emit('recognition_result', {'text': '实时识别已停止'})
            print('实时识别已停止', file=sys.stderr)
        except subprocess.TimeoutExpired:
            recognition_process.kill()
            emit('recognition_result', {'text': '实时识别强制终止'})
            print('实时识别强制终止', file=sys.stderr)
        except Exception as e:
            emit('recognition_result', {'error': f'停止识别失败：{str(e)}'})
            print(f'停止识别失败：{str(e)}', file=sys.stderr)
        recognition_process = None
    else:
        emit('recognition_result', {'error': '无正在运行的识别进程'})
        print('错误：无正在运行的识别进程', file=sys.stderr)

# API：启动训练
@app.route('/start_training', methods=['POST'])
def start_training():
    global training_process
    data = request.json
    model_path = os.path.join(TRAIN_MODEL_ROOT, data.get('model'))
    dataset_path = data.get('dataset_path')
    training_params = data.get('training_params', {})
    
    if not os.path.exists(model_path):
        return jsonify({"error": "无效的模型路径"}), 400
    if not os.path.exists(dataset_path):
        return jsonify({"error": "无效的数据集路径"}), 400
    
    with process_lock:
        if training_process is not None and training_process.poll() is None:
            return jsonify({"error": "训练已经在运行"}), 400
        
        cmd = [
            "conda", "run", "-n", "asr_train_env", "--no-capture-output", "python", "train.py",
            "--model_path", model_path,
            "--dataset_path", dataset_path,
            "--output_dir", SAVE_MODEL_ROOT,
            "--per_device_train_batch_size", str(training_params.get('per_device_train_batch_size', 2)),
            "--gradient_accumulation_steps", str(training_params.get('gradient_accumulation_steps', 1)),
            "--num_train_epochs", str(training_params.get('num_train_epochs', 1)),
            "--learning_rate", str(training_params.get('learning_rate', 1e-5)),
            "--fp16", str(training_params.get('fp16', False)).lower()
        ]
        
        def run_training():
            global training_process
            training_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                bufsize=1,
                text=True,
                encoding="utf-8"
            )
            def read_stream(stream):
                for line in iter(stream.readline, ''):
                    log_queue.put(line.strip())
                stream.close()
            t1 = threading.Thread(target=read_stream, args=(training_process.stdout,))
            t2 = threading.Thread(target=read_stream, args=(training_process.stderr,))
            t1.start()
            t2.start()
            training_process.wait()
            t1.join()
            t2.join()
            log_queue.put("[训练完成]")
        
        threading.Thread(target=run_training, daemon=True).start()
        return jsonify({"status": "success", "message": "训练已开始"})

@app.route('/stop_training', methods=['POST'])
def stop_training():
    global training_process
    with process_lock:
        if training_process is None or training_process.poll() is not None:
            return jsonify({"message": "没有正在运行的训练进程"})
        try:
            training_process.terminate()
            training_process.wait(timeout=5)
            log_queue.put("[训练已停止]")
            return jsonify({"message": "训练已停止"})
        except Exception as e:
            return jsonify({"error": f"停止训练失败：{str(e)}"}), 500
        finally:
            training_process = None

def stream_logs():
    while True:
        log = log_queue.get()
        yield f"data: {log}\n\n"
        if log in ("[训练完成]", "[训练已停止]"):
            break

@app.route('/stream_logs', methods=['GET'])
def stream_logs_endpoint():
    return Response(stream_logs(), mimetype='text/event-stream')

# WebSocket：启动语音合成
@socketio.on('start_tts')
def start_tts(data):
    global tts_process
    model = data.get('model')
    text = data.get('text')
    params = data.get('params', {})
    if not model or not text:
        emit('tts_result', {'error': '缺少模型或文本'})
        print('错误：缺少模型或文本', file=sys.stderr)
        return

    # 直接拼接模型路径
    model_path = os.path.join(TTS_MODEL_ROOT, model)

    conda_env_name = "tts_new_env"
    conda_activate = "/home/believe/anaconda3/bin/activate"
    if not os.path.exists(conda_activate):
        emit('tts_result', {'error': f'Anaconda 激活脚本未找到：{conda_activate}'})
        print(f'错误：Anaconda 激活脚本未找到：{conda_activate}', file=sys.stderr)
        return

    output_filename = f"output_{int(time.time())}.wav"
    output_path = os.path.join(SAVE_AUDIO_ROOT, output_filename)
    cmd = f'. "{conda_activate}" {conda_env_name} && python speech_synthesis.py "{model_path}" "{text}" {params.get("speech_rate", 1.0)} {params.get("volume", 1.0)} "{params.get("pitch", "normal")}" "{params.get("emotion_tone", "calm")}" "{params.get("voice", "zhiyan_emo")}" "{output_path}"'

    try:
        if tts_process and tts_process.poll() is None:
            emit('tts_result', {'error': '已有正在运行的语音合成进程'})
            print('错误：已有正在运行的语音合成进程', file=sys.stderr)
            return
        print(f"执行命令: {cmd}", file=sys.stderr)
        tts_process = subprocess.Popen(
            ["/bin/bash", "-c", cmd],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8'
        )
        emit('tts_result', {'text': '开始语音合成'})
        print('开始语音合成', file=sys.stderr)
        socketio.start_background_task(read_tts_output, output_filename)
    except Exception as e:
        error_msg = f'语音合成子进程启动失败：{str(e)}'
        emit('tts_result', {'error': error_msg})
        print(error_msg, file=sys.stderr)

# WebSocket：停止语音合成
@socketio.on('stop_tts')
def stop_tts():
    global tts_process
    if tts_process and tts_process.poll() is None:
        tts_process.terminate()
        try:
            tts_process.wait(timeout=2)
            emit('tts_result', {'text': '语音合成已停止'})
            print('语音合成已停止', file=sys.stderr)
        except subprocess.TimeoutExpired:
            tts_process.kill()
            emit('tts_result', {'text': '语音合成强制终止'})
            print('语音合成强制终止', file=sys.stderr)
        tts_process = None
    else:
        emit('tts_result', {'error': '无正在运行的语音合成进程'})
        print('错误：无正在运行的语音合成进程', file=sys.stderr)

# 异步读取实时识别输出
def read_recognition_output():
    global recognition_process
    print(f"开始监控实时识别子进程 (recognition_seq2seq.py) 状态 (PID: {recognition_process.pid})", file=sys.stderr)
    while recognition_process and recognition_process.poll() is None:
        try:
            output = recognition_process.stdout.readline().strip()
            error = recognition_process.stderr.readline().strip()
            if output:
                print(f"实时识别子进程输出: {output}", file=sys.stderr)
                socketio.emit('recognition_result', {'text': output})
            if error:
                print(f"实时识别子进程错误: {error}", file=sys.stderr)
                socketio.emit('recognition_result', {'error': error})
        except Exception as e:
            print(f"读取实时识别子进程输出失败: {str(e)}", file=sys.stderr)
            socketio.emit('recognition_result', {'error': f'读取识别输出失败：{str(e)}'})
        time.sleep(0.1)
    
    if recognition_process:
        return_code = recognition_process.poll()
        print(f"实时识别子进程已终止 (PID: {recognition_process.pid}, 退出码: {return_code})", file=sys.stderr)
        try:
            stdout, stderr = recognition_process.communicate(timeout=2)
            if stdout:
                print(f"实时识别子进程最终输出: {stdout.strip()}", file=sys.stderr)
                socketio.emit('recognition_result', {'text': stdout.strip()})
            if stderr:
                print(f"实时识别子进程最终错误: {stderr.strip()}", file=sys.stderr)
                socketio.emit('recognition_result', {'error': stderr.strip()})
        except subprocess.TimeoutExpired:
            print("实时识别子进程通信超时，已强制终止", file=sys.stderr)
            recognition_process.kill()
            socketio.emit('recognition_result', {'text': '实时识别子进程通信超时，已强制终止'})
        except Exception as e:
            print(f"实时识别子进程通信失败: {str(e)}", file=sys.stderr)
            socketio.emit('recognition_result', {'error': f'通信失败：{str(e)}'})
        recognition_process = None



# 异步读取语音合成输出
def read_tts_output(output_filename):
    global tts_process
    # 忽略的非错误消息关键词
    ignore_messages = [
        "modelscope - INFO",
        "modelscope - WARNING",
        "FutureWarning",
        "torch.load",
        "weight_norm",
        "WeightNorm.apply"  # 添加 WeightNorm.apply
    ]
    while tts_process and tts_process.poll() is None:
        try:
            output = tts_process.stdout.readline().strip()
            error = tts_process.stderr.readline().strip()
            if output:
                print(f'语音合成输出: {output}', file=sys.stderr)
                socketio.emit('tts_result', {'text': output, 'audio': output_filename})
            if error and not any(msg in error for msg in ignore_messages):
                print(f'语音合成错误: {error}', file=sys.stderr)
                socketio.emit('tts_result', {'error': error})
            elif error:
                print(f'语音合成调试信息: {error}', file=sys.stderr)  # 仅记录调试信息
        except Exception as e:
            error_msg = f'读取语音合成输出失败：{str(e)}'
            print(error_msg, file=sys.stderr)
            socketio.emit('tts_result', {'error': error_msg})
        time.sleep(0.01)

    try:
        stdout, stderr = tts_process.communicate(timeout=2)
        return_code = tts_process.returncode
        print(f'语音合成子进程结束，退出码: {return_code}', file=sys.stderr)
        stdout_lines = [line.strip() for line in stdout.splitlines() if line.strip()]
        stderr_lines = [line.strip() for line in stderr.splitlines() if line.strip()]
        for line in stdout_lines:
            print(f'语音合成最终输出: {line}', file=sys.stderr)
            socketio.emit('tts_result', {'text': line, 'audio': output_filename})
        for line in stderr_lines:
            if not any(msg in line for msg in ignore_messages):
                print(f'语音合成最终错误: {line}', file=sys.stderr)
                socketio.emit('tts_result', {'error': line})
            else:
                print(f'语音合成最终调试信息: {line}', file=sys.stderr)
        if return_code != 0:
            error_msg = f'语音合成子进程失败，退出码: {return_code}'
            print(error_msg, file=sys.stderr)
            socketio.emit('tts_result', {'error': error_msg})
    except Exception as e:
        error_msg = f'读取语音合成最终输出失败：{str(e)}'
        print(error_msg, file=sys.stderr)
        socketio.emit('tts_result', {'error': error_msg})
    finally:
        tts_process = None

@app.route('/list_voice_models', methods=['GET'])
def list_voice_models():
    model_dir = TTS_VOICE_MODEL_ROOT  # 使用语音克隆模型路径
    try:
        models = [d for d in os.listdir(model_dir) if os.path.isdir(os.path.join(model_dir, d))]
        print(f"语音克隆模型列表: {models}", file=sys.stderr)
        return jsonify(models)
    except Exception as e:
        print(f"获取语音克隆模型列表失败: {str(e)}", file=sys.stderr)
        return jsonify({'error': str(e)}), 500

# 新添加：上传语音克隆音频的路由
@app.route('/upload_clone_audio', methods=['POST'])
def upload_clone_audio():
    if 'clone_audio' not in request.files:
        return jsonify({"error": "没有提供音频文件"}), 400
    file = request.files['clone_audio']
    if file.filename == '':
        return jsonify({"error": "文件名为空"}), 400
    if not file.filename.endswith(('.wav', '.mp3')):
        return jsonify({"error": "文件格式不支持，请上传 .wav 或 .mp3 文件"}), 400

    # 生成唯一文件名
    file_id = str(uuid.uuid4())
    file_extension = os.path.splitext(file.filename)[1]
    filename = f"clone_audio_{file_id}{file_extension}"
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    
    try:
        file.save(file_path)
        print(f"音频上传成功: {file_path}", file=sys.stderr)
        return jsonify({"message": "音频上传成功", "path": file_path})
    except Exception as e:
        print(f"上传失败: {str(e)}", file=sys.stderr)
        return jsonify({"error": f"上传失败：{str(e)}"}), 500

# 新添加：启动语音克隆的 WebSocket 处理器
@socketio.on('start_clone')
def handle_start_clone(data):
    global tts_process
    model_path = data.get('model_path')
    audio_path = data.get('audio_path')
    synth_text = data.get('synth_text')
    lang_tip = data.get('lang_tip', 'zh')

    # 拼接完整模型路径
    model_full_path = os.path.join(TTS_VOICE_MODEL_ROOT, model_path)
    print(f"检查模型路径: {model_full_path}", file=sys.stderr)
    if not os.path.exists(model_full_path):
        print(f"错误: 模型路径 {model_full_path} 不存在", file=sys.stderr)
        emit('clone_result', {'error': f'模型路径 {model_path} 不存在'})
        return

    if not audio_path or not os.path.exists(audio_path):
        print(f"错误: 音频路径 {audio_path} 不存在", file=sys.stderr)
        emit('clone_result', {'error': f'音频路径 {audio_path} 不存在'})
        return

    print(f"开始语音克隆: 模型={model_full_path}, 音频={audio_path}, 文本={synth_text}, 语言={lang_tip}", file=sys.stderr)

    conda_env_name = "voice"
    conda_activate = "/home/believe/anaconda3/bin/activate"
    if not os.path.exists(conda_activate):
        print(f"错误: Anaconda 激活脚本未找到: {conda_activate}", file=sys.stderr)
        emit('clone_result', {'error': f'Anaconda 激活脚本未找到：{conda_activate}'})
        return

    output_filename = f"tts_output_{uuid.uuid4().hex}.wav"
    output_path = os.path.join(SAVE_AUDIO_ROOT, output_filename)
    cmd = f'. "{conda_activate}" {conda_env_name} && python voice.py "{model_full_path}" "{audio_path}" "{synth_text}" "{lang_tip}" "{output_path}"'

    try:
        print(f"执行命令: {cmd}", file=sys.stderr)
        tts_process = subprocess.Popen(
            ["/bin/bash", "-c", cmd],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8'
        )
        emit('clone_result', {'text': '语音克隆任务已启动'})
        while True:
            output = tts_process.stdout.readline()
            if output == '' and tts_process.poll() is not None:
                break
            if output:
                print(f"克隆输出: {output.strip()}", file=sys.stderr)
                emit('clone_result', {'text': output.strip()})

        stderr_output = tts_process.stderr.read()
        if tts_process.returncode != 0:
            print(f"克隆失败: {stderr_output}", file=sys.stderr)
            emit('clone_result', {'error': f'克隆失败：{stderr_output}'})
            return

        if os.path.exists(output_path):
            emit('clone_result', {'text': '语音克隆完成', 'audio_path': output_filename})
        else:
            emit('clone_result', {'error': '输出音频文件未生成'})
    except Exception as e:
        print(f"克隆异常: {str(e)}", file=sys.stderr)
        emit('clone_result', {'error': f'克隆异常：{str(e)}'})

if __name__ == '__main__':
    socketio.run(app, debug=True)