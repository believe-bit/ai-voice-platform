<!-- views/ExperimentProjects.vue -->
<template>
  <div class="experiment-projects">
    <el-container>
      <el-aside width="250px" class="experiment-sidebar">
        <el-menu
          :default-active="activeExperiment"
          class="experiment-menu"
          @select="handleExperimentSelect"
        >
          <el-menu-item
            v-for="experiment in experiments"
            :key="experiment.id"
            :index="experiment.id"
          >
            <span>{{ experiment.name }}</span>
          </el-menu-item>
        </el-menu>
      </el-aside>
      <el-main class="experiment-content">
        <h2>{{ currentExperimentName }}</h2>
        <div v-if="currentExperimentComponent">
          <component :is="currentExperimentComponent" />
        </div>
        <div v-else>
          <p>未找到实验组件</p>
        </div>
      </el-main>
    </el-container>
  </div>
</template>

<script>
import { ref, computed, nextTick } from 'vue';
import axios from 'axios';
import { ElMessage } from 'element-plus';

// 音频采集实验组件
const SpeechCollection = {
  template: `
    <div class="speech-collection">
      <h3>音频采集实验</h3>
      <el-select v-model="selectedFormat" placeholder="选择音频格式">
        <el-option label="WAV" value="wav"></el-option>
        <el-option label="MP3" value="mp3"></el-option>
      </el-select>
      <el-button type="primary" @click="startRecording" :disabled="isRecording">开始录音</el-button>
      <el-button type="danger" @click="stopRecording" :disabled="!isRecording">停止录音</el-button>
      <div v-if="audioUrl">
        <h4>录制音频：</h4>
        <audio :src="audioUrl" controls></audio>
        <el-button type="success" @click="downloadAudio">下载音频</el-button>
      </div>
      <p v-if="errorMessage" class="error">{{ errorMessage }}</p>
    </div>
  `,
  setup() {
    const selectedFormat = ref('wav');
    const isRecording = ref(false);
    const audioUrl = ref(null);
    const audioBlob = ref(null);
    const errorMessage = ref('');
    let mediaRecorder = null;
    let audioChunks = [];

    const startRecording = async () => {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        mediaRecorder = new MediaRecorder(stream, { mimeType: 'audio/webm' });
        audioChunks = [];
        mediaRecorder.ondataavailable = (event) => {
          if (event.data.size > 0) {
            audioChunks.push(event.data);
          }
        };
        mediaRecorder.onstop = async () => {
          audioBlob.value = new Blob(audioChunks, { type: 'audio/webm' });
          await uploadToServer();
          audioChunks = [];
        };
        mediaRecorder.start();
        isRecording.value = true;
        errorMessage.value = '';
      } catch (error) {
        errorMessage.value = `录音启动失败: ${error.message}`;
        console.error('录音启动失败:', error);
      }
    };

    const stopRecording = () => {
      if (mediaRecorder && mediaRecorder.state !== 'inactive') {
        mediaRecorder.stop();
        isRecording.value = false;
      }
    };

    const uploadToServer = async () => {
      if (!audioBlob.value) {
        errorMessage.value = '无音频数据可上传';
        return;
      }
      const formData = new FormData();
      formData.append('audio', audioBlob.value, `recording.webm`);
      formData.append('format', selectedFormat.value);
      try {
        const response = await axios.post('http://localhost:5000/save_recording', formData, {
          headers: { 'Content-Type': 'multipart/form-data' }
        });
        if (response.data.filename) {
          audioUrl.value = `http://localhost:5000/audio/${response.data.filename}`;
          errorMessage.value = '';
        } else {
          errorMessage.value = '服务器未返回音频文件路径';
        }
      } catch (error) {
        errorMessage.value = `上传失败: ${error.message}`;
        console.error('上传失败:', error);
      }
    };

    const downloadAudio = () => {
      if (audioUrl.value) {
        const a = document.createElement('a');
        a.href = audioUrl.value;
        a.download = `recording.${selectedFormat.value}`;
        a.click();
      }
    };

    return {
      selectedFormat,
      isRecording,
      audioUrl,
      startRecording,
      stopRecording,
      downloadAudio,
      errorMessage,
    };
  },
};

// 语音波形显示实验组件
const WaveformDisplay = {
  template: `
    <div class="waveform-display">
      <h3>语音波形显示实验</h3>
      <el-upload
        action=""
        :http-request="handleUpload"
        accept=".wav,.mp3"
        :show-file-list="false"
        :before-upload="beforeUpload"
      >
        <el-button type="primary">选择音频文件</el-button>
      </el-upload>
      <el-button type="success" @click="displayWaveform" :disabled="!audioFile">显示波形</el-button>
      <div v-if="audioUrl">
        <h4>已上传音频：</h4>
        <audio :src="audioUrl" controls></audio>
      </div>
      <canvas ref="waveformCanvas" width="800" height="200" v-if="showWaveform"></canvas>
      <p v-if="errorMessage" class="error">{{ errorMessage }}</p>
    </div>
  `,
  setup() {
    const audioFile = ref(null);
    const audioUrl = ref(null);
    const showWaveform = ref(false);
    const waveformCanvas = ref(null);
    const errorMessage = ref('');

    const beforeUpload = (file) => {
      const maxSize = 10 * 1024 * 1024; // 10MB
      if (file.size > maxSize) {
        errorMessage.value = '文件大小超过 10MB';
        return false;
      }
      if (!file.name.endsWith('.wav') && !file.name.endsWith('.mp3')) {
        errorMessage.value = '请上传 .wav 或 .mp3 格式的音频文件';
        return false;
      }
      return true;
    };

    const handleUpload = async (upload) => {
      const file = upload.file;
      audioFile.value = file;
      audioUrl.value = URL.createObjectURL(file);
      showWaveform.value = false;
      errorMessage.value = '';

      // 上传文件到后端
      const formData = new FormData();
      formData.append('audio', file);
      try {
        const response = await axios.post('http://localhost:5000/upload_waveform_audio', formData, {
          headers: { 'Content-Type': 'multipart/form-data' }
        });
        console.log('音频上传响应:', response.data);
      } catch (error) {
        errorMessage.value = `音频上传失败: ${error.message}`;
        console.error('音频上传失败:', error);
      }
    };

    const displayWaveform = async () => {
      if (!audioFile.value) {
        errorMessage.value = '请先选择音频文件';
        return;
      }

      try {
        const formData = new FormData();
        formData.append('audio', audioFile.value);
        const response = await axios.post('http://localhost:5000/process_waveform', formData, {
          headers: { 'Content-Type': 'multipart/form-data' }
        });

        if (response.data.waveform) {
          showWaveform.value = true;
          await nextTick(); // 使用 nextTick 确保 DOM 更新
          if (!waveformCanvas.value) {
            errorMessage.value = 'Canvas 元素未正确渲染';
            console.error('Canvas 引用为 null');
            return;
          }
          drawWaveform(response.data.waveform);
          errorMessage.value = '';
        } else {
          errorMessage.value = '服务器未返回波形数据';
        }
      } catch (error) {
        errorMessage.value = `波形生成失败: ${error.message}`;
        console.error('波形生成失败:', error);
      }
    };

    const drawWaveform = (waveformData) => {
      console.log('波形数据:', waveformData); // 调试波形数据
      if (!waveformCanvas.value) {
        errorMessage.value = '无法绘制波形：Canvas 未找到';
        console.error('Canvas 未找到');
        return;
      }
      const canvas = waveformCanvas.value;
      const ctx = canvas.getContext('2d');
      if (!ctx) {
        errorMessage.value = '无法获取 Canvas 上下文';
        console.error('无法获取 Canvas 上下文');
        return;
      }
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      ctx.beginPath();
      ctx.strokeStyle = '#409EFF';
      ctx.lineWidth = 2;

      const width = canvas.width;
      const height = canvas.height;
      const samples = waveformData.length;
      const step = width / samples;

      for (let i = 0; i < samples; i++) {
        const x = i * step;
        const y = ((1 - waveformData[i]) * height) / 2; // 归一化数据到画布高度
        if (i == 0) {
          ctx.moveTo(x, y);
        } else {
          ctx.lineTo(x, y);
        }
      }
      ctx.stroke();
    };

    return {
      audioFile,
      audioUrl,
      showWaveform,
      waveformCanvas,
      errorMessage,
      beforeUpload,
      handleUpload,
      displayWaveform,
    };
  },
};

// 语音编码实验组件
const SpeechEncoding = {
  template: `
    <div class="speech-encoding">
      <h3>语音编码实验</h3>
      <el-upload
        action=""
        :http-request="handleUpload"
        accept=".wav,.mp3"
        :show-file-list="false"
        :before-upload="beforeUpload"
      >
        <el-button type="primary">选择音频文件</el-button>
      </el-upload>
      <el-select v-model="encodingFormat" placeholder="选择编码方式">
        <el-option label="PCM" value="pcm"></el-option>
        <el-option label="MP3" value="mp3"></el-option>
        <el-option label="AAC" value="aac"></el-option>
      </el-select>
      <el-button type="success" @click="encodeAudio" :disabled="!audioFile || !encodingFormat">开始编码</el-button>
      <div v-if="audioUrl">
        <h4>已上传音频：</h4>
        <audio :src="audioUrl" controls></audio>
      </div>
      <div v-if="encodingResult">
        <h4>编码结果：</h4>
        <el-input
          type="textarea"
          :rows="4"
          v-model="encodingResult"
          readonly
        ></el-input>
        <el-button type="primary" @click="downloadEncodedAudio" v-if="encodedAudioUrl">下载编码后的音频</el-button>
      </div>
      <p v-if="errorMessage" class="error">{{ errorMessage }}</p>
    </div>
  `,
  setup() {
    const audioFile = ref(null);
    const audioUrl = ref(null);
    const encodingFormat = ref('');
    const encodingResult = ref('');
    const encodedAudioUrl = ref('');
    const errorMessage = ref('');

    const beforeUpload = (file) => {
      const maxSize = 10 * 1024 * 1024; // 10MB
      if (file.size > maxSize) {
        errorMessage.value = '文件大小超过 10MB';
        return false;
      }
      if (!file.name.endsWith('.wav') && !file.name.endsWith('.mp3')) {
        errorMessage.value = '请上传 .wav 或 .mp3 格式的音频文件';
        return false;
      }
      return true;
    };

    const handleUpload = async (upload) => {
      const file = upload.file;
      audioFile.value = file;
      audioUrl.value = URL.createObjectURL(file);
      encodingResult.value = '';
      encodedAudioUrl.value = '';
      errorMessage.value = '';
    };

    const encodeAudio = async () => {
      if (!audioFile.value) {
        errorMessage.value = '请先选择音频文件';
        return;
      }
      if (!encodingFormat.value) {
        errorMessage.value = '请选择编码方式';
        return;
      }

      try {
        const formData = new FormData();
        formData.append('audio', audioFile.value);
        formData.append('format', encodingFormat.value);
        const response = await axios.post('http://localhost:5000/encode_audio', formData, {
          headers: { 'Content-Type': 'multipart/form-data' }
        });

        if (response.data.message && response.data.filename) {
          encodingResult.value = `编码成功！文件保存为: ${response.data.filename}\n下载链接: ${response.data.url}`;
          encodedAudioUrl.value = response.data.url;
          errorMessage.value = '';
        } else {
          encodingResult.value = '';
          errorMessage.value = '服务器未返回编码结果';
        }
      } catch (error) {
        encodingResult.value = '';
        errorMessage.value = `编码失败: ${error.message}`;
        console.error('编码失败:', error);
      }
    };

    const downloadEncodedAudio = () => {
      if (encodedAudioUrl.value) {
        const a = document.createElement('a');
        a.href = encodedAudioUrl.value;
        a.download = encodedAudioUrl.value.split('/').pop();
        a.click();
      }
    };

    return {
      audioFile,
      audioUrl,
      encodingFormat,
      encodingResult,
      encodedAudioUrl,
      errorMessage,
      beforeUpload,
      handleUpload,
      encodeAudio,
      downloadEncodedAudio,
    };
  },
};

// 语音采样频率转换实验组件
const SamplingFrequency = {
  template: `
    <div class="sampling-frequency">
      <h3>语音采样频率转换实验</h3>
      <el-upload
        action=""
        :http-request="handleUpload"
        accept=".wav,.mp3"
        :show-file-list="false"
        :before-upload="beforeUpload"
      >
        <el-button type="primary">选择音频文件</el-button>
      </el-upload>
      <el-select v-model="sampleRate" placeholder="选择采样率">
        <el-option label="8000 Hz" value="8000"></el-option>
        <el-option label="16000 Hz" value="16000"></el-option>
        <el-option label="22050 Hz" value="22050"></el-option>
        <el-option label="44100 Hz" value="44100"></el-option>
        <el-option label="48000 Hz" value="48000"></el-option>
      </el-select>
      <el-button type="success" @click="convertSampleRate" :disabled="!audioFile || !sampleRate">开始转换</el-button>
      <div v-if="audioUrl">
        <h4>已上传音频：</h4>
        <audio :src="audioUrl" controls></audio>
      </div>
      <div v-if="conversionResult">
        <h4>转换结果：</h4>
        <el-input
          type="textarea"
          :rows="4"
          v-model="conversionResult"
          readonly
        ></el-input>
        <div v-if="convertedAudioUrl">
          <h4>转换后的音频：</h4>
          <audio :src="convertedAudioUrl" controls></audio>
          <el-button type="primary" @click="downloadConvertedAudio">下载转换后的音频</el-button>
        </div>
      </div>
      <p v-if="errorMessage" class="error">{{ errorMessage }}</p>
    </div>
  `,
  setup() {
    const audioFile = ref(null);
    const audioUrl = ref(null);
    const sampleRate = ref('');
    const conversionResult = ref('');
    const convertedAudioUrl = ref('');
    const errorMessage = ref('');

    const beforeUpload = (file) => {
      const maxSize = 10 * 1024 * 1024; // 10MB
      if (file.size > maxSize) {
        errorMessage.value = '文件大小超过 10MB';
        return false;
      }
      if (!file.name.endsWith('.wav') && !file.name.endsWith('.mp3')) {
        errorMessage.value = '请上传 .wav 或 .mp3 格式的音频文件';
        return false;
      }
      return true;
    };

    const handleUpload = async (upload) => {
      const file = upload.file;
      audioFile.value = file;
      audioUrl.value = URL.createObjectURL(file);
      conversionResult.value = '';
      convertedAudioUrl.value = '';
      errorMessage.value = '';
    };

    const convertSampleRate = async () => {
      if (!audioFile.value) {
        errorMessage.value = '请先选择音频文件';
        return;
      }
      if (!sampleRate.value) {
        errorMessage.value = '请选择采样率';
        return;
      }

      try {
        const formData = new FormData();
        formData.append('audio', audioFile.value);
        formData.append('sample_rate', sampleRate.value);
        const response = await axios.post('http://localhost:5000/convert_sample_rate', formData, {
          headers: { 'Content-Type': 'multipart/form-data' }
        });

        if (response.data.message && response.data.filename) {
          conversionResult.value = `采样率转换成功！文件保存为: ${response.data.filename}\n新采样率: ${response.data.sample_rate} Hz\n下载链接: ${response.data.url}`;
          convertedAudioUrl.value = response.data.url;
          errorMessage.value = '';
        } else {
          conversionResult.value = '';
          errorMessage.value = '服务器未返回转换结果';
        }
      } catch (error) {
        conversionResult.value = '';
        errorMessage.value = `采样率转换失败: ${error.message}`;
        console.error('采样率转换失败:', error);
      }
    };

    const downloadConvertedAudio = () => {
      if (convertedAudioUrl.value) {
        const a = document.createElement('a');
        a.href = convertedAudioUrl.value;
        a.download = convertedAudioUrl.value.split('/').pop();
        a.click();
      }
    };

    return {
      audioFile,
      audioUrl,
      sampleRate,
      conversionResult,
      convertedAudioUrl,
      errorMessage,
      beforeUpload,
      handleUpload,
      convertSampleRate,
      downloadConvertedAudio,
    };
  },
};

// 语音信号强度实验组件
const SignalStrength = {
  template: `
    <div class="signal-strength">
      <h3>语音信号强度实验</h3>
      <el-upload
        action=""
        :http-request="handleUpload"
        accept=".wav,.mp3"
        :show-file-list="false"
        :before-upload="beforeUpload"
      >
        <el-button type="primary">选择音频文件</el-button>
      </el-upload>
      <el-button type="success" @click="analyzeSignalStrength" :disabled="!audioFile">信号检测</el-button>
      <div v-if="audioUrl">
        <h4>已上传音频：</h4>
        <audio :src="audioUrl" controls></audio>
      </div>
      <canvas ref="signalCanvas" width="800" height="200" v-if="showSignalGraph"></canvas>
      <p v-if="errorMessage" class="error">{{ errorMessage }}</p>
    </div>
  `,
  setup() {
    const audioFile = ref(null);
    const audioUrl = ref(null);
    const showSignalGraph = ref(false);
    const signalCanvas = ref(null);
    const errorMessage = ref('');

    const beforeUpload = (file) => {
      const maxSize = 10 * 1024 * 1024; // 10MB
      if (file.size > maxSize) {
        errorMessage.value = '文件大小超过 10MB';
        return false;
      }
      if (!file.name.endsWith('.wav') && !file.name.endsWith('.mp3')) {
        errorMessage.value = '请上传 .wav 或 .mp3 格式的音频文件';
        return false;
      }
      return true;
    };

    const handleUpload = async (upload) => {
      const file = upload.file;
      audioFile.value = file;
      audioUrl.value = URL.createObjectURL(file);
      showSignalGraph.value = false;
      errorMessage.value = '';
    };

    const analyzeSignalStrength = async () => {
      if (!audioFile.value) {
        errorMessage.value = '请先选择音频文件';
        return;
      }

      try {
        const formData = new FormData();
        formData.append('audio', audioFile.value);
        const response = await axios.post('http://localhost:5000/analyze_signal_strength', formData, {
          headers: { 'Content-Type': 'multipart/form-data' }
        });

        if (response.data.time_points && response.data.rms_values) {
          showSignalGraph.value = true;
          await nextTick(); // 确保 DOM 更新
          if (!signalCanvas.value) {
            errorMessage.value = 'Canvas 元素未正确渲染';
            console.error('Canvas 引用为 null');
            return;
          }
          drawSignalGraph(response.data.time_points, response.data.rms_values);
          errorMessage.value = '';
        } else {
          errorMessage.value = '服务器未返回信号强度数据';
        }
      } catch (error) {
        errorMessage.value = `信号强度分析失败: ${error.message}`;
        console.error('信号强度分析失败:', error);
      }
    };

    const drawSignalGraph = (timePoints, rmsValues) => {
      console.log('信号强度数据:', { timePoints, rmsValues }); // 调试数据
      if (!signalCanvas.value) {
        errorMessage.value = '无法绘制信号强度图：Canvas 未找到';
        console.error('Canvas 未找到');
        return;
      }
      const canvas = signalCanvas.value;
      const ctx = canvas.getContext('2d');
      if (!ctx) {
        errorMessage.value = '无法获取 Canvas 上下文';
        console.error('无法获取 Canvas 上下文');
        return;
      }
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      // 设置画布样式
      ctx.strokeStyle = '#409EFF';
      ctx.lineWidth = 2;
      ctx.beginPath();

      // 坐标轴
      ctx.strokeStyle = '#000000';
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.moveTo(50, 20);
      ctx.lineTo(50, 180);
      ctx.lineTo(750, 180);
      ctx.stroke();
      ctx.font = '12px Arial';
      ctx.fillText('分贝 (dB)', 10, 20);
      ctx.fillText('时间 (s)', 750, 195);

      // 绘制分贝刻度
      const minDb = -96; // 静音底线
      const maxDb = 0;   // 最大分贝
      for (let db = minDb; db <= maxDb; db += 24) {
        const y = 180 - ((db - minDb) / (maxDb - minDb)) * 160;
        ctx.beginPath();
        ctx.moveTo(45, y);
        ctx.lineTo(50, y);
        ctx.stroke();
        ctx.fillText(`${db}`, 20, y + 4);
      }

      // 绘制时间刻度
      const maxTime = Math.max(...timePoints);
      for (let t = 0; t <= maxTime; t += maxTime / 5) {
        const x = 50 + (t / maxTime) * 700;
        ctx.beginPath();
        ctx.moveTo(x, 180);
        ctx.lineTo(x, 185);
        ctx.stroke();
        ctx.fillText(t.toFixed(1), x - 10, 195);
      }

      // 绘制信号强度曲线
      ctx.strokeStyle = '#409EFF';
      ctx.lineWidth = 2;
      ctx.beginPath();
      const width = 700; // 画布宽度（留出轴的空间）
      const height = 160; // 画布高度（留出轴的空间）
      const numPoints = timePoints.length;

      for (let i = 0; i < numPoints; i++) {
        const x = 50 + (timePoints[i] / maxTime) * width;
        const y = 180 - ((rmsValues[i] - minDb) / (maxDb - minDb)) * height;
        if (i === 0) {
          ctx.moveTo(x, y);
        } else {
          ctx.lineTo(x, y);
        }
      }
      ctx.stroke();
    };

    return {
      audioFile,
      audioUrl,
      showSignalGraph,
      signalCanvas,
      errorMessage,
      beforeUpload,
      handleUpload,
      analyzeSignalStrength,
    };
  },
};

// 白噪音信号实验组件
const WhiteNoise = {
  template: `
    <div class="white-noise">
      <h3>白噪音信号实验</h3>
      <el-button type="primary" @click="generateWhiteNoise" :disabled="isGenerating">生成白噪音</el-button>
      <el-button type="success" @click="playWhiteNoise" :disabled="!whiteNoiseUrl || isPlaying">播放白噪音</el-button>
      <el-button type="danger" @click="stopWhiteNoise" :disabled="!isPlaying">停止播放</el-button>
      <div v-if="whiteNoiseUrl">
        <h4>生成的白噪音音频：</h4>
        <audio ref="audioPlayer" :src="whiteNoiseUrl"></audio>
      </div>
      <canvas ref="strengthCanvas" width="800" height="200" v-if="showStrengthGraph"></canvas>
      <p v-if="errorMessage" class="error">{{ errorMessage }}</p>
    </div>
  `,
  setup() {
    const isGenerating = ref(false);
    const whiteNoiseUrl = ref(null);
    const isPlaying = ref(false);
    const showStrengthGraph = ref(false);
    const strengthCanvas = ref(null);
    const audioPlayer = ref(null);
    const errorMessage = ref('');
    let strengthData = []; // 记录信号强度数据
    let strengthInterval = null; // 定时器

    const generateWhiteNoise = async () => {
      isGenerating.value = true;
      try {
        const response = await axios.get('http://localhost:5000/generate_white_noise');
        if (response.data.filename) {
          whiteNoiseUrl.value = `http://localhost:5000/audio/${response.data.filename}`;
          showStrengthGraph.value = false;
          strengthData = [];
          errorMessage.value = '';
          ElMessage.success('白噪音生成成功！'); // 添加成功提示
        } else {
          errorMessage.value = '服务器未返回白噪音文件';
        }
      } catch (error) {
        errorMessage.value = `生成白噪音失败: ${error.message}`;
        console.error('生成白噪音失败:', error);
      } finally {
        isGenerating.value = false;
      }
    };

    const playWhiteNoise = () => {
      if (audioPlayer.value) {
        audioPlayer.value.play();
        isPlaying.value = true;
        // 开始记录信号强度（模拟，每 50ms 记录一次）
        strengthData = [];
        strengthInterval = setInterval(recordStrength, 50);
      }
    };

    const stopWhiteNoise = () => {
      if (audioPlayer.value) {
        audioPlayer.value.pause();
        audioPlayer.value.currentTime = 0;
        isPlaying.value = false;
        if (strengthInterval) {
          clearInterval(strengthInterval);
          strengthInterval = null;
        }
        drawStrengthGraph();
      }
    };

    const recordStrength = () => {
      // 模拟记录白噪音强度（白噪音强度恒定，约 -20 dB 到 -10 dB 随机）
      const db = -20 + Math.random() * 10; // 模拟白噪音强度
      strengthData.push(db);
      if (strengthData.length > 800) {
        strengthData.shift(); // 保持数据点不超过 800
      }
    };

    const drawStrengthGraph = async () => {
      showStrengthGraph.value = true;
      await nextTick(); // 确保 Canvas 渲染
      if (!strengthCanvas.value) {
        errorMessage.value = 'Canvas 元素未正确渲染';
        console.error('Canvas 引用为 null');
        return;
      }
      const canvas = strengthCanvas.value;
      const ctx = canvas.getContext('2d');
      if (!ctx) {
        errorMessage.value = '无法获取 Canvas 上下文';
        console.error('无法获取 Canvas 上下文');
        return;
      }
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      ctx.beginPath();
      ctx.strokeStyle = '#409EFF';
      ctx.lineWidth = 2;

      const width = canvas.width;
      const height = canvas.height;
      const samples = strengthData.length;
      const step = width / samples;

      for (let i = 0; i < samples; i++) {
        const x = i * step;
        const y = (1 - (strengthData[i] + 96) / 96) * height / 2; // 归一化分贝到画布高度 (-96 to 0 dB)
        if (i === 0) {
          ctx.moveTo(x, y);
        } else {
          ctx.lineTo(x, y);
        }
      }
      ctx.stroke();
    };

    return {
      isGenerating,
      whiteNoiseUrl,
      isPlaying,
      showStrengthGraph,
      strengthCanvas,
      audioPlayer,
      errorMessage,
      generateWhiteNoise,
      playWhiteNoise,
      stopWhiteNoise,
    };
  },
};

// 短时傅里叶变换实验组件（占位，假设已有实现）
const ShortTimeFourier = {
  template: `
    <div class="short-time-fourier">
      <h3>语音短时傅里叶变换实验</h3>
      <el-upload
        action=""
        :http-request="handleUpload"
        accept=".wav,.mp3"
        :show-file-list="false"
        :before-upload="beforeUpload"
      >
        <el-button type="primary">上传音频文件</el-button>
      </el-upload>
      <el-select
        v-model="windowType"
        placeholder="选择窗口类型"
        :disabled="!audioFile"
        style="margin: 10px;"
      >
        <el-option label="汉明窗" value="hamming"></el-option>
        <el-option label="汉宁窗" value="hann"></el-option>
        <el-option label="矩形窗" value="rectangular"></el-option>
      </el-select>
      <el-input-number
        v-model="frameLength"
        :min="128"
        :max="2048"
        :step="1"
        placeholder="帧长"
        :disabled="!audioFile"
        style="margin: 10px;"
      ></el-input-number>
      <el-input-number
        v-model="hopLength"
        :min="32"
        :max="1024"
        :step="1"
        placeholder="帧移"
        :disabled="!audioFile"
        style="margin: 10px;"
      ></el-input-number>
      <el-input-number
        v-model="nFft"
        :min="128"
        :max="4096"
        :step="1"
        placeholder="FFT 点数"
        :disabled="!audioFile"
        style="margin: 10px;"
      ></el-input-number>
      <el-button
        type="success"
        @click="analyzeSTFT"
        :disabled="!audioFile || !windowType || !frameLength || !hopLength || !nFft || isProcessing"
      >
        开始分析
      </el-button>
      <div v-if="audioUrl">
        <h4>原始音频</h4>
        <audio :src="audioUrl" controls @error="handleAudioError"></audio>
      </div>
      <div v-if="originalWaveform">
        <h4>原始波形</h4>
        <canvas ref="waveformCanvas" width="800" height="200"></canvas>
      </div>
      <div v-if="spectrogramData">
        <h4>短时傅里叶变换频谱图</h4>
        <canvas ref="spectrogramCanvas" width="800" height="400"></canvas>
      </div>
      <el-alert v-if="errorMessage" type="error" :title="errorMessage" :closable="false" />
    </div>
  `,
  setup() {
    const audioFile = ref(null);
    const audioUrl = ref(null);
    const windowType = ref('');
    const frameLength = ref(256);
    const hopLength = ref(128);
    const nFft = ref(256);
    const originalWaveform = ref(null);
    const spectrogramData = ref(null);
    const waveformCanvas = ref(null);
    const spectrogramCanvas = ref(null);
    const isProcessing = ref(false);
    const errorMessage = ref('');

    const beforeUpload = (file) => {
      const maxSize = 10 * 1024 * 1024; // 10MB
      if (file.size > maxSize) {
        errorMessage.value = '文件大小超过 10MB';
        return false;
      }
      if (!file.name.endsWith('.wav') && !file.name.endsWith('.mp3')) {
        errorMessage.value = '请上传 .wav 或 .mp3 格式的音频文件';
        return false;
      }
      return true;
    };

    const handleUpload = async (upload) => {
      audioFile.value = upload.file;
      audioUrl.value = URL.createObjectURL(upload.file);
      windowType.value = '';
      frameLength.value = 256;
      hopLength.value = 128;
      nFft.value = 256;
      originalWaveform.value = null;
      spectrogramData.value = null;
      errorMessage.value = '';
    };

    const handleAudioError = (e) => {
      errorMessage.value = `音频加载失败: ${e.target.error.message}`;
      console.error('音频加载失败:', e.target.error);
    };

    const analyzeSTFT = async () => {
      if (!audioFile.value) {
        errorMessage.value = '请先上传音频文件';
        return;
      }
      if (!windowType.value) {
        errorMessage.value = '请选择窗口类型';
        return;
      }
      if (!frameLength.value || !hopLength.value || !nFft.value) {
        errorMessage.value = '请输入有效的帧长、帧移和 FFT 点数';
        return;
      }
      isProcessing.value = true;
      try {
        const formData = new FormData();
        formData.append('audio', audioFile.value);
        formData.append('window_type', windowType.value);
        formData.append('frame_length', frameLength.value);
        formData.append('hop_length', hopLength.value);
        formData.append('n_fft', nFft.value);

        const response = await axios.post('http://localhost:5000/short_time_fourier', formData, {
          headers: { 'Content-Type': 'multipart/form-data' }
        });

        if (response.data.waveform && response.data.spectrogram) {
          originalWaveform.value = response.data.waveform;
          spectrogramData.value = response.data.spectrogram;
          await nextTick();
          if (waveformCanvas.value) {
            drawWaveform(waveformCanvas.value, originalWaveform.value);
          } else {
            errorMessage.value = '波形 Canvas 未初始化';
            console.error('waveformCanvas 引用为 null');
          }
          if (spectrogramCanvas.value) {
            drawSpectrogram(spectrogramCanvas.value, spectrogramData.value);
          } else {
            errorMessage.value = '频谱图 Canvas 未初始化';
            console.error('spectrogramCanvas 引用为 null');
          }
          errorMessage.value = '';
          ElMessage.success('短时傅里叶变换完成！');
        } else {
          errorMessage.value = '服务器未返回完整结果';
          console.error('服务器响应:', response.data);
        }
      } catch (error) {
        let errorMsg = '短时傅里叶变换失败';
        if (error.response) {
          errorMsg = `短时傅里叶变换失败: ${error.response.data.error || error.message}`;
        } else if (error.request) {
          errorMsg = '短时傅里叶变换失败: 无法连接到服务器，请检查后端服务';
        } else {
          errorMsg = `短时傅里叶变换失败: ${error.message}`;
        }
        errorMessage.value = errorMsg;
        console.error('短时傅里叶变换失败:', error);
      } finally {
        isProcessing.value = false;
      }
    };

    const drawWaveform = (canvasEl, data) => {
      if (!canvasEl || !data || data.length === 0) {
        errorMessage.value = '无法绘制波形：Canvas 或数据缺失';
        console.error('无法绘制波形', { canvasEl, data });
        return;
      }
      const canvas = canvasEl;
      const ctx = canvas.getContext('2d');
      if (!ctx) {
        errorMessage.value = '无法绘制波形：无法获取 Canvas 上下文';
        console.error('无法绘制波形：Canvas 上下文未找到');
        return;
      }
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      ctx.beginPath();
      ctx.strokeStyle = '#409EFF';
      ctx.lineWidth = 2;

      const width = canvas.width;
      const height = canvas.height;
      const samples = Math.min(data.length, 1000);
      const step = data.length / samples;

      for (let i = 0; i < samples; i++) {
        const index = Math.floor(i * step);
        const x = i * (width / samples);
        const y = ((1 - data[index]) * height) / 2;
        if (i === 0) {
          ctx.moveTo(x, y);
        } else {
          ctx.lineTo(x, y);
        }
      }
      ctx.stroke();
    };

    const drawSpectrogram = (canvasEl, data) => {
      if (!canvasEl || !data || !data.length) {
        errorMessage.value = '无法绘制频谱图：Canvas 或数据缺失';
        console.error('无法绘制频谱图', { canvasEl, data });
        return;
      }
      const canvas = canvasEl;
      const ctx = canvas.getContext('2d');
      if (!ctx) {
        errorMessage.value = '无法绘制频谱图：无法获取 Canvas 上下文';
        console.error('无法绘制频谱图：Canvas 上下文未找到');
        return;
      }
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      const width = canvas.width;
      const height = canvas.height;
      const freqBins = data[0].length;
      const timeFrames = data.length;
      const imageData = ctx.createImageData(width, height);

      // 线性插值调整数据尺寸
      const xStep = timeFrames / width;
      const yStep = freqBins / height;

      // 计算最大和最小幅度用于归一化
      let maxAmp = -Infinity;
      let minAmp = Infinity;
      for (let t = 0; t < timeFrames; t++) {
        for (let f = 0; f < freqBins; f++) {
          const amp = data[t][f];
          if (amp > maxAmp) maxAmp = amp;
          if (amp < minAmp) minAmp = amp;
        }
      }
      const ampRange = maxAmp - minAmp || 1;

      // 绘制热力图
      for (let x = 0; x < width; x++) {
        for (let y = 0; y < height; y++) {
          const t = Math.min(Math.floor(x * xStep), timeFrames - 1);
          const f = Math.min(Math.floor((height - y - 1) * yStep), freqBins - 1);
          const amp = data[t][f];
          const normalized = (amp - minAmp) / ampRange;

          // 转换为颜色（蓝到红）
          const r = Math.floor(normalized * 255);
          const g = Math.floor((1 - normalized) * 255);
          const b = 0;
          const index = (y * width + x) * 4;
          imageData.data[index] = r;
          imageData.data[index + 1] = g;
          imageData.data[index + 2] = b;
          imageData.data[index + 3] = 255; // Alpha
        }
      }
      ctx.putImageData(imageData, 0, 0);
    };

    return {
      audioFile,
      audioUrl,
      windowType,
      frameLength,
      hopLength,
      nFft,
      originalWaveform,
      spectrogramData,
      waveformCanvas,
      spectrogramCanvas,
      isProcessing,
      errorMessage,
      beforeUpload,
      handleUpload,
      handleAudioError,
      analyzeSTFT,
    };
  },
};

// 音频自动增益控制实验组件
const AutoGainControl = {
  template: `
    <div class="auto-gain-control">
      <h3>音频自动增益控制实验</h3>
      <el-upload
        action=""
        :http-request="handleUpload"
        accept=".wav,.mp3"
        :show-file-list="false"
        :before-upload="beforeUpload"
      >
        <el-button type="primary">上传音频文件</el-button>
      </el-upload>
      <div v-if="audioUrl">
        <h4>已上传音频：</h4>
        <audio :src="audioUrl" controls></audio>
      </div>
      <el-switch v-model="enableAGC" active-text="启用 AGC" inactive-text="禁用 AGC"></el-switch>
      <el-button type="success" @click="playProcessedAudio" :disabled="!audioFile || isPlaying">播放处理后的音频</el-button>
      <el-button type="danger" @click="stopAudio" :disabled="!isPlaying">停止播放</el-button>
      <div>
        <h4>处理后的音频：</h4>
        <audio ref="audioPlayer" :src="processedAudioUrl" controls></audio>
      </div>
      <div v-if="originalWaveform">
        <h4>原始音频波形</h4>
        <canvas ref="originalCanvas" width="800" height="200"></canvas>
      </div>
      <div v-if="processedWaveform">
        <h4>处理后音频波形</h4>
        <canvas ref="processedCanvas" width="800" height="200"></canvas>
      </div>
      <div v-if="gainStats">
        <h4>增益调整统计信息</h4>
        <p>平均增益: {{ gainStats.average ? gainStats.average.toFixed(2) : 'N/A' }} dB</p>
        <p>最大增益: {{ gainStats.max ? gainStats.max.toFixed(2) : 'N/A' }} dB</p>
        <p>最小增益: {{ gainStats.min ? gainStats.min.toFixed(2) : 'N/A' }} dB</p>
      </div>
      <p v-if="errorMessage" class="error">{{ errorMessage }}</p>
    </div>
  `,
  setup() {
    const audioFile = ref(null);
    const audioUrl = ref(null);
    const processedAudioUrl = ref(null);
    const enableAGC = ref(true);
    const isPlaying = ref(false);
    const originalWaveform = ref(null);
    const processedWaveform = ref(null);
    const gainStats = ref(null);
    const originalCanvas = ref(null);
    const processedCanvas = ref(null);
    const audioPlayer = ref(null);
    const errorMessage = ref('');

    const beforeUpload = (file) => {
      const maxSize = 10 * 1024 * 1024; // 10MB
      if (file.size > maxSize) {
        errorMessage.value = '文件大小超过 10MB';
        return false;
      }
      if (!file.name.endsWith('.wav') && !file.name.endsWith('.mp3')) {
        errorMessage.value = '请上传 .wav 或 .mp3 格式的音频文件';
        return false;
      }
      return true;
    };

    const handleUpload = async (upload) => {
      audioFile.value = upload.file;
      audioUrl.value = URL.createObjectURL(upload.file);
      processedAudioUrl.value = null;
      originalWaveform.value = null;
      processedWaveform.value = null;
      gainStats.value = null;
      isPlaying.value = false;
      errorMessage.value = '';
    };

    const playProcessedAudio = async () => {
      if (!audioFile.value) {
        errorMessage.value = '请先上传音频文件';
        return;
      }
      isPlaying.value = true;
      try {
        const formData = new FormData();
        formData.append('audio', audioFile.value);
        formData.append('enable_agc', enableAGC.value);
        const response = await axios.post('http://localhost:5000/apply_agc', formData, {
          headers: { 'Content-Type': 'multipart/form-data' }
        });

        if (response.data.message && response.data.filename) {
          processedAudioUrl.value = `http://localhost:5000/audio/${response.data.filename}`;
          await nextTick(); // 等待 DOM 更新
          if (!audioPlayer.value) {
            errorMessage.value = '音频播放器未初始化';
            console.error('audioPlayer 引用为 null');
            return;
          }
          audioPlayer.value.src = processedAudioUrl.value;
          audioPlayer.value.play();
          originalWaveform.value = response.data.original_waveform;
          processedWaveform.value = response.data.processed_waveform;
          gainStats.value = response.data.gain_stats;
          await nextTick();
          drawWaveform(originalCanvas.value, originalWaveform.value, '原始音频');
          drawWaveform(processedCanvas.value, processedWaveform.value, '处理后音频');
          ElMessage.success('音频处理成功，已开始播放！');
        } else {
          errorMessage.value = '服务器未返回处理结果';
          console.error('服务器响应:', response.data);
        }
      } catch (error) {
        errorMessage.value = `处理失败: ${error.message}`;
        console.error('音频处理失败:', error);
      } finally {
        isPlaying.value = false;
      }
    };

    const stopAudio = () => {
      if (audioPlayer.value) {
        audioPlayer.value.pause();
        audioPlayer.value.currentTime = 0;
        isPlaying.value = false;
      } else {
        errorMessage.value = '音频播放器未初始化';
        console.error('audioPlayer 引用为 null');
      }
    };

    const drawWaveform = (canvasEl, data, title) => {
      if (!canvasEl || !data) {
        errorMessage.value = `无法绘制${title}波形：Canvas 或数据缺失`;
        console.error(`无法绘制${title}波形`, { canvasEl, data });
        return;
      }
      const canvas = canvasEl;
      const ctx = canvas.getContext('2d');
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      ctx.beginPath();
      ctx.strokeStyle = '#409EFF';
      ctx.lineWidth = 2;

      const width = canvas.width;
      const height = canvas.height;
      const samples = data.length;
      const step = width / samples;

      const maxVal = Math.max(...data.map(Math.abs)) || 1;
      for (let i = 0; i < samples; i++) {
        const x = i * step;
        const y = ((1 - data[i] / maxVal) * height) / 2;
        if (i === 0) {
          ctx.moveTo(x, y);
        } else {
          ctx.lineTo(x, y);
        }
      }
      ctx.stroke();
    };

    return {
      audioFile,
      audioUrl,
      processedAudioUrl,
      enableAGC,
      isPlaying,
      originalWaveform,
      processedWaveform,
      gainStats,
      originalCanvas,
      processedCanvas,
      audioPlayer,
      errorMessage,
      beforeUpload,
      handleUpload,
      playProcessedAudio,
      stopAudio,
    };
  },
};

const EndpointDetection = {
  template: `
    <div class="endpoint-detection">
      <h3>语音端点检测实验</h3>
      <el-upload
        action=""
        :http-request="handleUpload"
        accept=".wav,.mp3"
        :show-file-list="false"
        :before-upload="beforeUpload"
      >
        <el-button type="primary">上传音频文件</el-button>
      </el-upload>
      <el-button type="success" @click="detectEndpoints" :disabled="!audioFile || isDetecting">开始检测</el-button>
      <div v-if="audioUrl">
        <h4>原始音频：</h4>
        <audio :src="audioUrl" controls @error="handleAudioError"></audio>
      </div>
      <div v-if="originalWaveform">
        <h4>原始音频波形</h4>
        <canvas ref="originalCanvas" width="800" height="200"></canvas>
      </div>
      <div v-for="(segment, index) in speechSegments" :key="index">
        <h4>语音段 {{ index + 1 }} 波形 (开始: {{ segment.start }}s, 结束: {{ segment.end }}s, 持续: {{ segment.duration }}s)</h4>
        <canvas :ref="el => setSegmentCanvas(index, el)" width="800" height="200"></canvas>
      </div>
      <el-alert v-if="errorMessage" type="error" :title="errorMessage" :closable="false" />
    </div>
  `,
  setup() {
    const audioFile = ref(null);
    const audioUrl = ref(null);
    const originalWaveform = ref(null);
    const speechSegments = ref([]);
    const originalCanvas = ref(null);
    const segmentCanvases = ref([]);
    const isDetecting = ref(false);
    const errorMessage = ref('');

    const beforeUpload = (file) => {
      const maxSize = 10 * 1024 * 1024; // 10MB
      if (file.size > maxSize) {
        errorMessage.value = '文件大小超过 10MB';
        return false;
      }
      if (!file.name.endsWith('.wav') && !file.name.endsWith('.mp3')) {
        errorMessage.value = '请上传 .wav 或 .mp3 格式的音频文件';
        return false;
      }
      return true;
    };

    const handleUpload = async (upload) => {
      audioFile.value = upload.file;
      audioUrl.value = URL.createObjectURL(upload.file);
      originalWaveform.value = null;
      speechSegments.value = [];
      segmentCanvases.value = [];
      errorMessage.value = '';
    };

    const setSegmentCanvas = (index, el) => {
      if (el) {
        segmentCanvases.value[index] = el;
      }
    };

    const handleAudioError = (e) => {
      errorMessage.value = `音频加载失败: ${e.target.error.message}`;
      console.error('音频加载失败:', e.target.error);
    };

    const detectEndpoints = async () => {
      if (!audioFile.value) {
        errorMessage.value = '请先上传音频文件';
        return;
      }
      isDetecting.value = true;
      try {
        const formData = new FormData();
        formData.append('audio', audioFile.value);
        const response = await axios.post('http://localhost:5000/detect_endpoints', formData, {
          headers: { 'Content-Type': 'multipart/form-data' }
        });

        if (response.data.original_waveform && response.data.speech_segments) {
          originalWaveform.value = response.data.original_waveform;
          speechSegments.value = response.data.speech_segments;
          segmentCanvases.value = new Array(speechSegments.value.length).fill(null); // 初始化 Canvas 数组
          await nextTick(); // 等待 DOM 更新
          await nextTick(); // 额外等待，确保 Canvas refs 就绪
          if (originalCanvas.value) {
            drawWaveform(originalCanvas.value, originalWaveform.value, '原始音频');
          } else {
            errorMessage.value = '原始波形 Canvas 未初始化';
            console.error('originalCanvas 引用为 null');
          }
          speechSegments.value.forEach((segment, index) => {
            const segmentCanvas = segmentCanvases.value[index];
            if (segmentCanvas && segment.waveform) {
              drawWaveform(segmentCanvas, segment.waveform, `语音段 ${index + 1}`);
            } else {
              errorMessage.value = `语音段 ${index + 1} Canvas 或波形数据缺失`;
              console.error(`segmentCanvas[${index}] 或 waveform 无效`, {
                segmentCanvas,
                waveform: segment.waveform
              });
            }
          });
          errorMessage.value = '';
          ElMessage.success('端点检测完成！');
        } else {
          errorMessage.value = '服务器未返回有效检测结果';
          console.error('服务器响应:', response.data);
        }
      } catch (error) {
        let errorMsg = '检测失败';
        if (error.response) {
          errorMsg = `检测失败: ${error.response.data.error || error.message}`;
        } else if (error.request) {
          errorMsg = '检测失败: 无法连接到服务器，请检查后端服务';
        } else {
          errorMsg = `检测失败: ${error.message}`;
        }
        errorMessage.value = errorMsg;
        console.error('端点检测失败:', error);
      } finally {
        isDetecting.value = false;
      }
    };

    const drawWaveform = (canvasEl, data, title) => {
      if (!canvasEl || !data || data.length === 0) {
        errorMessage.value = `无法绘制${title}波形：Canvas 或数据缺失`;
        console.error(`无法绘制${title}波形`, { canvasEl, data });
        return;
      }
      const canvas = canvasEl;
      const ctx = canvas.getContext('2d');
      if (!ctx) {
        errorMessage.value = `无法绘制${title}波形：无法获取 Canvas 上下文`;
        console.error(`无法绘制${title}波形：Canvas 上下文未找到`);
        return;
      }
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      ctx.beginPath();
      ctx.strokeStyle = '#409EFF';
      ctx.lineWidth = 2;

      const width = canvas.width;
      const height = canvas.height;
      const samples = Math.min(data.length, 1000);
      const step = data.length / samples;

      for (let i = 0; i < samples; i++) {
        const index = Math.floor(i * step);
        const x = i * (width / samples);
        const y = ((1 - data[index]) * height) / 2; // 数据归一化到 [-1, 1]
        if (i === 0) {
          ctx.moveTo(x, y);
        } else {
          ctx.lineTo(x, y);
        }
      }
      ctx.stroke();
    };

    return {
      audioFile,
      audioUrl,
      originalWaveform,
      speechSegments,
      originalCanvas,
      segmentCanvases,
      isDetecting,
      errorMessage,
      beforeUpload,
      handleUpload,
      setSegmentCanvas,
      handleAudioError,
      detectEndpoints,
    };
  },
};

const NoiseClassification = {
  template: `
    <div class="noise-classification">
      <h3>语音噪音类实验</h3>
      <el-upload
        action=""
        :http-request="handleUpload"
        accept=".wav,.mp3"
        :show-file-list="false"
        :before-upload="beforeUpload"
      >
        <el-button type="primary">上传音频文件</el-button>
      </el-upload>
      <el-select v-model="noiseType" placeholder="选择噪音类型">
        <el-option label="白噪音" value="white"></el-option>
        <el-option label="粉红噪音" value="pink"></el-option>
        <el-option label="环境噪音" value="ambient"></el-option>
      </el-select>
      <el-slider v-model="noiseIntensity" :min="0" :max="100" show-input></el-slider>
      <el-button type="success" @click="analyzeNoise" :disabled="!audioFile || !noiseType">开始分析</el-button>
      <div v-if="audioUrl">
        <h4>原始音频：</h4>
        <audio :src="audioUrl" controls></audio>
      </div>
      <div v-if="originalWaveform">
        <h4>原始音频波形</h4>
        <canvas ref="originalCanvas" width="800" height="200"></canvas>
      </div>
      <div v-if="noisyWaveform">
        <h4>添加噪音后的音频波形</h4>
        <canvas ref="noisyCanvas" width="800" height="200"></canvas>
      </div>
      <div v-if="noiseWaveform">
        <h4>添加的噪音波形</h4>
        <canvas ref="noiseCanvas" width="800" height="200"></canvas>
      </div>
      <div v-if="snr">
        <h4>信噪比 (SNR): {{ snr.toFixed(2) }} dB</h4>
      </div>
      <div v-if="impactDescription">
        <h4>噪声对语音质量的影响</h4>
        <p>{{ impactDescription }}</p>
      </div>
      <p v-if="errorMessage" class="error">{{ errorMessage }}</p>
    </div>
  `,
  setup() {
    const audioFile = ref(null);
    const audioUrl = ref(null);
    const noiseType = ref('');
    const noiseIntensity = ref(50);
    const originalWaveform = ref(null);
    const noisyWaveform = ref(null);
    const noiseWaveform = ref(null);
    const snr = ref(null);
    const impactDescription = ref('');
    const originalCanvas = ref(null);
    const noisyCanvas = ref(null);
    const noiseCanvas = ref(null);
    const errorMessage = ref('');

    const beforeUpload = (file) => {
      const maxSize = 10 * 1024 * 1024; // 10MB
      if (file.size > maxSize) {
        errorMessage.value = '文件大小超过 10MB';
        return false;
      }
      if (!file.name.endsWith('.wav') && !file.name.endsWith('.mp3')) {
        errorMessage.value = '请上传 .wav 或 .mp3 格式的音频文件';
        return false;
      }
      return true;
    };

    const handleUpload = async (upload) => {
      audioFile.value = upload.file;
      audioUrl.value = URL.createObjectURL(upload.file);
      originalWaveform.value = null;
      noisyWaveform.value = null;
      noiseWaveform.value = null;
      snr.value = null;
      impactDescription.value = '';
      errorMessage.value = '';
    };

    const analyzeNoise = async () => {
      if (!audioFile.value) {
        errorMessage.value = '请先上传音频文件';
        return;
      }
      if (!noiseType.value) {
        errorMessage.value = '请选择噪音类型';
        return;
      }
      try {
        const formData = new FormData();
        formData.append('audio', audioFile.value);
        formData.append('noise_type', noiseType.value);
        formData.append('noise_intensity', noiseIntensity.value / 100); // 转换为 0-1 范围
        const response = await axios.post('http://localhost:5000/analyze_noise', formData, {
          headers: { 'Content-Type': 'multipart/form-data' }
        });

        if (response.data.original_waveform && response.data.noisy_waveform && response.data.noise_waveform && response.data.snr) {
          originalWaveform.value = response.data.original_waveform;
          noisyWaveform.value = response.data.noisy_waveform;
          noiseWaveform.value = response.data.noise_waveform;
          snr.value = response.data.snr;
          impactDescription.value = response.data.impact_description;
          await nextTick();
          drawWaveform(originalCanvas.value, originalWaveform.value);
          drawWaveform(noisyCanvas.value, noisyWaveform.value);
          drawWaveform(noiseCanvas.value, noiseWaveform.value);
          errorMessage.value = '';
          ElMessage.success('噪音分析完成！');
        } else {
          errorMessage.value = '服务器未返回完整分析结果';
        }
      } catch (error) {
        errorMessage.value = `分析失败: ${error.message}`;
        console.error('噪音分析失败:', error);
      }
    };

    const drawWaveform = (canvasEl, data) => {
      if (!canvasEl || !data) return;
      const canvas = canvasEl;
      const ctx = canvas.getContext('2d');
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      ctx.beginPath();
      ctx.strokeStyle = '#409EFF';
      ctx.lineWidth = 2;

      const width = canvas.width;
      const height = canvas.height;
      const samples = data.length;
      const step = width / samples;

      for (let i = 0; i < samples; i++) {
        const x = i * step;
        const y = (data[i] + 1) * height / 2; // 假设数据已归一化到 [-1, 1]
        if (i === 0) {
          ctx.moveTo(x, y);
        } else {
          ctx.lineTo(x, y);
        }
      }
      ctx.stroke();
    };

    return {
      audioFile,
      audioUrl,
      noiseType,
      noiseIntensity,
      originalWaveform,
      noisyWaveform,
      noiseWaveform,
      snr,
      impactDescription,
      originalCanvas,
      noisyCanvas,
      noiseCanvas,
      errorMessage,
      beforeUpload,
      handleUpload,
      analyzeNoise,
    };
  },
};

const SpeechEnhancement = {
  template: `
    <div class="speech-enhancement">
      <h3>语音增强实验</h3>
      <el-upload
        action=""
        :http-request="handleUpload"
        accept=".wav,.mp3"
        :show-file-list="false"
        :before-upload="beforeUpload"
      >
        <el-button type="primary">上传音频文件</el-button>
      </el-upload>
      <el-select v-model="algorithm" placeholder="选择增强算法" :disabled="!audioFile">
        <el-option label="谱减法" value="spectral_subtraction"></el-option>
        <el-option label="Wiener滤波" value="wiener"></el-option>
      </el-select>
      <el-button
        type="success"
        @click="enhanceSpeech"
        :disabled="!audioFile || !algorithm || isProcessing"
      >
        增强处理
      </el-button>
      <div v-if="audioUrl">
        <h4>原始音频</h4>
        <audio :src="audioUrl" controls @error="handleAudioError"></audio>
      </div>
      <div v-if="originalWaveform">
        <h4>原始音频波形</h4>
        <canvas ref="originalCanvas" width="800" height="200"></canvas>
      </div>
      <div v-if="enhancedWaveform">
        <h4>增强后音频波形</h4>
        <canvas ref="enhancedCanvas" width="800" height="200"></canvas>
      </div>
      <div v-if="comparisonResult">
        <h4>增强前后对比效果</h4>
        <p>{{ comparisonResult }}</p>
      </div>
      <el-alert v-if="errorMessage" type="error" :title="errorMessage" :closable="false" />
    </div>
  `,
  setup() {
    const audioFile = ref(null);
    const audioUrl = ref(null);
    const algorithm = ref('');
    const originalWaveform = ref(null);
    const enhancedWaveform = ref(null);
    const comparisonResult = ref('');
    const originalCanvas = ref(null);
    const enhancedCanvas = ref(null);
    const isProcessing = ref(false);
    const errorMessage = ref('');

    const beforeUpload = (file) => {
      const maxSize = 10 * 1024 * 1024; // 10MB
      if (file.size > maxSize) {
        errorMessage.value = '文件大小超过 10MB';
        return false;
      }
      if (!file.name.endsWith('.wav') && !file.name.endsWith('.mp3')) {
        errorMessage.value = '请上传 .wav 或 .mp3 格式的音频文件';
        return false;
      }
      return true;
    };

    const handleUpload = async (upload) => {
      audioFile.value = upload.file;
      audioUrl.value = URL.createObjectURL(upload.file);
      algorithm.value = '';
      originalWaveform.value = null;
      enhancedWaveform.value = null;
      comparisonResult.value = '';
      errorMessage.value = '';
    };

    const handleAudioError = (e) => {
      errorMessage.value = `音频加载失败: ${e.target.error.message}`;
      console.error('音频加载失败:', e.target.error);
    };

    const enhanceSpeech = async () => {
      if (!audioFile.value) {
        errorMessage.value = '请先上传音频文件';
        return;
      }
      if (!algorithm.value) {
        errorMessage.value = '请选择增强算法';
        return;
      }
      isProcessing.value = true;
      try {
        const formData = new FormData();
        formData.append('audio', audioFile.value);
        formData.append('algorithm', algorithm.value);
        const response = await axios.post('http://localhost:5000/enhance_speech', formData, {
          headers: { 'Content-Type': 'multipart/form-data' }
        });

        if (response.data.original_waveform && response.data.enhanced_waveform && response.data.comparison_result) {
          originalWaveform.value = response.data.original_waveform;
          enhancedWaveform.value = response.data.enhanced_waveform;
          comparisonResult.value = response.data.comparison_result;
          await nextTick();
          if (originalCanvas.value) {
            drawWaveform(originalCanvas.value, originalWaveform.value, '原始波形');
          } else {
            errorMessage.value = '原始波形 Canvas 未初始化';
            console.error('originalCanvas 引用为 null');
          }
          if (enhancedCanvas.value) {
            drawWaveform(enhancedCanvas.value, enhancedWaveform.value, '增强后波形');
          } else {
            errorMessage.value = '增强后波形 Canvas 未初始化';
            console.error('enhancedCanvas 引用为 null');
          }
          errorMessage.value = '';
          ElMessage.success('语音增强完成！');
        } else {
          errorMessage.value = '服务器未返回完整增强结果';
          console.error('服务器响应:', response.data);
        }
      } catch (error) {
        let errorMsg = '增强失败';
        if (error.response) {
          errorMsg = `增强失败: ${error.response.data.error || error.message}`;
        } else if (error.request) {
          errorMsg = '增强失败: 无法连接到服务器，请检查后端服务';
        } else {
          errorMsg = `增强失败: ${error.message}`;
        }
        errorMessage.value = errorMsg;
        console.error('语音增强失败:', error);
      } finally {
        isProcessing.value = false;
      }
    };

    const drawWaveform = (canvasEl, data, title) => {
      if (!canvasEl || !data || data.length === 0) {
        errorMessage.value = `无法绘制${title}：Canvas 或数据缺失`;
        console.error(`无法绘制${title}`, { canvasEl, data });
        return;
      }
      const canvas = canvasEl;
      const ctx = canvas.getContext('2d');
      if (!ctx) {
        errorMessage.value = `无法绘制${title}：无法获取 Canvas 上下文`;
        console.error(`无法绘制${title}：Canvas 上下文未找到`);
        return;
      }
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      ctx.beginPath();
      ctx.strokeStyle = '#409EFF';
      ctx.lineWidth = 2;

      const width = canvas.width;
      const height = canvas.height;
      const samples = Math.min(data.length, 1000); // 限制最大点数
      const step = data.length / samples;

      for (let i = 0; i < samples; i++) {
        const index = Math.floor(i * step);
        const x = i * (width / samples);
        const y = ((1 - data[index]) * height) / 2; // 数据归一化到 [-1, 1]
        if (i === 0) {
          ctx.moveTo(x, y);
        } else {
          ctx.lineTo(x, y);
        }
      }
      ctx.stroke();
    };

    return {
      audioFile,
      audioUrl,
      algorithm,
      originalWaveform,
      enhancedWaveform,
      comparisonResult,
      originalCanvas,
      enhancedCanvas,
      isProcessing,
      errorMessage,
      beforeUpload,
      handleUpload,
      handleAudioError,
      enhanceSpeech,
    };
  },
};

const AddNoise = {
  template: `
    <div class="add-noise">
      <h3>语音添加噪音实验</h3>
      <el-upload
        action=""
        :http-request="handleUpload"
        accept=".wav,.mp3"
        :show-file-list="false"
        :before-upload="beforeUpload"
      >
        <el-button type="primary">上传音频文件</el-button>
      </el-upload>
      <el-select v-model="noiseType" placeholder="选择噪音类型" :disabled="!audioFile">
        <el-option label="白噪音" value="white"></el-option>
        <el-option label="粉红噪音" value="pink"></el-option>
        <el-option label="环境噪音" value="ambient"></el-option>
      </el-select>
      <el-slider v-model="noiseIntensity" :min="0" :max="100" show-input :disabled="!audioFile"></el-slider>
      <el-button type="success" @click="addNoise" :disabled="!audioFile || !noiseType || isProcessing">添加噪音</el-button>
      <div v-if="audioUrl">
        <h4>原始音频：</h4>
        <audio :src="audioUrl" controls @error="handleAudioError"></audio>
      </div>
      <div v-if="noisyAudioUrl">
        <h4>添加噪音后的音频：</h4>
        <audio :src="noisyAudioUrl" controls @error="handleAudioError"></audio>
        <a :href="noisyAudioUrl" download="noisy_audio.wav">下载带噪音频</a>
      </div>
      <div v-if="originalWaveform">
        <h4>原始音频波形</h4>
        <canvas ref="originalCanvas" width="800" height="200"></canvas>
      </div>
      <div v-if="noisyWaveform">
        <h4>添加噪音后的音频波形</h4>
        <canvas ref="noisyCanvas" width="800" height="200"></canvas>
      </div>
      <div v-if="noiseWaveform">
        <h4>添加的噪音波形</h4>
        <canvas ref="noiseCanvas" width="800" height="200"></canvas>
      </div>
      <div v-if="snr !== null">
        <h4>信噪比 (SNR): {{ snr.toFixed(2) }} dB</h4>
      </div>
      <div v-if="impactDescription">
        <h4>噪声对语音质量的影响</h4>
        <p>{{ impactDescription }}</p>
      </div>
      <el-alert v-if="errorMessage" type="error" :title="errorMessage" :closable="false" />
    </div>
  `,
  setup() {
    const audioFile = ref(null);
    const audioUrl = ref(null);
    const noiseType = ref('');
    const noiseIntensity = ref(50);
    const originalWaveform = ref(null);
    const noisyWaveform = ref(null);
    const noiseWaveform = ref(null);
    const snr = ref(null);
    const impactDescription = ref('');
    const noisyAudioUrl = ref(null);
    const originalCanvas = ref(null);
    const noisyCanvas = ref(null);
    const noiseCanvas = ref(null);
    const isProcessing = ref(false);
    const errorMessage = ref('');

    const beforeUpload = (file) => {
      const maxSize = 10 * 1024 * 1024; // 10MB
      if (file.size > maxSize) {
        errorMessage.value = '文件大小超过 10MB';
        return false;
      }
      if (!file.name.endsWith('.wav') && !file.name.endsWith('.mp3')) {
        errorMessage.value = '请上传 .wav 或 .mp3 格式的音频文件';
        return false;
      }
      return true;
    };

    const handleUpload = async (upload) => {
      audioFile.value = upload.file;
      audioUrl.value = URL.createObjectURL(upload.file);
      noiseType.value = '';
      noiseIntensity.value = 50;
      originalWaveform.value = null;
      noisyWaveform.value = null;
      noiseWaveform.value = null;
      snr.value = null;
      impactDescription.value = '';
      noisyAudioUrl.value = null;
      errorMessage.value = '';
    };

    const handleAudioError = (e) => {
      errorMessage.value = `音频加载失败: ${e.target.error.message}`;
      console.error('音频加载失败:', e.target.error);
    };

    const addNoise = async () => {
      if (!audioFile.value) {
        errorMessage.value = '请先上传音频文件';
        return;
      }
      if (!noiseType.value) {
        errorMessage.value = '请选择噪音类型';
        return;
      }
      isProcessing.value = true;
      try {
        const formData = new FormData();
        formData.append('audio', audioFile.value);
        formData.append('noise_type', noiseType.value);
        formData.append('noise_intensity', noiseIntensity.value / 100);
        const response = await axios.post('http://localhost:5000/add_noise', formData, {
          headers: { 'Content-Type': 'multipart/form-data' }
        });

        if (
          response.data.original_waveform &&
          response.data.noisy_waveform &&
          response.data.noise_waveform &&
          response.data.snr !== undefined &&
          response.data.impact_description &&
          response.data.noisy_filename
        ) {
          originalWaveform.value = response.data.original_waveform;
          noisyWaveform.value = response.data.noisy_waveform;
          noiseWaveform.value = response.data.noise_waveform;
          snr.value = response.data.snr;
          impactDescription.value = response.data.impact_description;
          noisyAudioUrl.value = `http://localhost:5000/audio/${response.data.noisy_filename}`;
          await nextTick();
          if (originalCanvas.value) {
            drawWaveform(originalCanvas.value, originalWaveform.value, '原始波形');
          } else {
            errorMessage.value = '原始波形 Canvas 未初始化';
            console.error('originalCanvas 引用为 null');
          }
          if (noisyCanvas.value) {
            drawWaveform(noisyCanvas.value, noisyWaveform.value, '带噪波形');
          } else {
            errorMessage.value = '带噪波形 Canvas 未初始化';
            console.error('noisyCanvas 引用为 null');
          }
          if (noiseCanvas.value) {
            drawWaveform(noiseCanvas.value, noiseWaveform.value, '噪音波形');
          } else {
            errorMessage.value = '噪音波形 Canvas 未初始化';
            console.error('noiseCanvas 引用为 null');
          }
          errorMessage.value = '';
          ElMessage.success('噪音添加完成！');
        } else {
          errorMessage.value = '服务器未返回完整结果';
          console.error('服务器响应:', response.data);
        }
      } catch (error) {
        let errorMsg = '添加噪音失败';
        if (error.response) {
          errorMsg = `添加噪音失败: ${error.response.data.error || error.message}`;
        } else if (error.request) {
          errorMsg = '添加噪音失败: 无法连接到服务器，请检查后端服务';
        } else {
          errorMsg = `添加噪音失败: ${error.message}`;
        }
        errorMessage.value = errorMsg;
        console.error('添加噪音失败:', error);
      } finally {
        isProcessing.value = false;
      }
    };

    const drawWaveform = (canvasEl, data, title) => {
      if (!canvasEl || !data || data.length === 0) {
        errorMessage.value = `无法绘制${title}：Canvas 或数据缺失`;
        console.error(`无法绘制${title}`, { canvasEl, data });
        return;
      }
      const canvas = canvasEl;
      const ctx = canvas.getContext('2d');
      if (!ctx) {
        errorMessage.value = `无法绘制${title}：无法获取 Canvas 上下文`;
        console.error(`无法绘制${title}：Canvas 上下文未找到`);
        return;
      }
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      ctx.beginPath();
      ctx.strokeStyle = '#409EFF';
      ctx.lineWidth = 2;

      const width = canvas.width;
      const height = canvas.height;
      const samples = Math.min(data.length, 1000);
      const step = data.length / samples;

      for (let i = 0; i < samples; i++) {
        const index = Math.floor(i * step);
        const x = i * (width / samples);
        const y = ((1 - data[index]) * height) / 2; // 数据归一化到 [-1, 1]
        if (i === 0) {
          ctx.moveTo(x, y);
        } else {
          ctx.lineTo(x, y);
        }
      }
      ctx.stroke();
    };

    return {
      audioFile,
      audioUrl,
      noiseType,
      noiseIntensity,
      originalWaveform,
      noisyWaveform,
      noiseWaveform,
      snr,
      impactDescription,
      noisyAudioUrl,
      originalCanvas,
      noisyCanvas,
      noiseCanvas,
      isProcessing,
      errorMessage,
      beforeUpload,
      handleUpload,
      handleAudioError,
      addNoise,
    };
  },
};

const EmotionAnalysis = {
  template: `
    <div class="emotion-analysis">
      <h3>情感分析实验</h3>
      <el-input
        v-model="inputText"
        type="textarea"
        :rows="4"
        placeholder="请输入待分析的中文文本"
        :maxlength="500"
        show-word-limit
      ></el-input>
      <el-button
        type="primary"
        @click="analyzeEmotion"
        :disabled="!inputText.trim() || isProcessing"
      >
        分析
      </el-button>
      <div v-if="emotionResult.length">
        <h4>情感分析结果</h4>
        <el-table :data="emotionResult" style="width: 100%; max-width: 600px">
          <el-table-column prop="label" label="情感标签"></el-table-column>
          <el-table-column prop="confidence" label="置信度" width="150">
            <template #default="scope">
              {{ (scope.row.confidence * 100).toFixed(2) }}%
            </template>
          </el-table-column>
        </el-table>
      </div>
      <el-alert v-if="errorMessage" type="error" :title="errorMessage" :closable="false" />
    </div>
  `,
  setup() {
    const inputText = ref('');
    const emotionResult = ref([]);
    const isProcessing = ref(false);
    const errorMessage = ref('');

    const analyzeEmotion = async () => {
      if (!inputText.value.trim()) {
        errorMessage.value = '请输入文本';
        return;
      }
      isProcessing.value = true;
      try {
        const response = await axios.post('http://localhost:5000/emotion_analysis', {
          text: inputText.value.trim()
        }, {
          headers: { 'Content-Type': 'application/json' }
        });

        if (response.data.emotion_result && Array.isArray(response.data.emotion_result)) {
          emotionResult.value = response.data.emotion_result;
          errorMessage.value = '';
          ElMessage.success('情感分析完成！');
        } else {
          errorMessage.value = '服务器未返回有效结果';
          console.error('服务器响应:', response.data);
        }
      } catch (error) {
        let errorMsg = '情感分析失败';
        if (error.response) {
          errorMsg = `情感分析失败: ${error.response.data.error || error.message}`;
        } else if (error.request) {
          errorMsg = '情感分析失败: 无法连接到服务器，请检查后端服务';
        } else {
          errorMsg = `情感分析失败: ${error.message}`;
        }
        errorMessage.value = errorMsg;
        console.error('情感分析失败:', error);
      } finally {
        isProcessing.value = false;
      }
    };

    return {
      inputText,
      emotionResult,
      isProcessing,
      errorMessage,
      analyzeEmotion
    };
  }
};

const RealTimeLocalization = {
  template: `
    <div class="real-time-localization">
      <h3>实时声源定位实验</h3>
      <el-button
        type="primary"
        @click="startLocalization"
        :disabled="isLocalizing"
      >
        开始定位
      </el-button>
      <el-button
        type="danger"
        @click="stopLocalization"
        :disabled="!isLocalizing"
      >
        停止定位
      </el-button>
      <div v-if="micWaveforms.length">
        <h4>麦克风阵列波形</h4>
        <div v-for="(waveform, index) in micWaveforms" :key="index">
          <p>麦克风 {{ index + 1 }}</p>
          <canvas :ref="'micCanvas' + index" width="800" height="100"></canvas>
        </div>
      </div>
      <div v-if="sourceDirection !== null">
        <h4>声源方向: {{ sourceDirection.toFixed(2) }}°</h4>
      </div>
      <div v-if="polarChart">
        <h4>声源位置（极坐标图）</h4>
        <canvas ref="polarCanvas" width="400" height="400"></canvas>
      </div>
      <el-alert v-if="errorMessage" type="error" :title="errorMessage" :closable="false" />
    </div>
  `,
  setup() {
    const isLocalizing = ref(false);
    const micWaveforms = ref([]);
    const sourceDirection = ref(null);
    const polarChart = ref(null);
    const polarCanvas = ref(null);
    const errorMessage = ref('');
    let socket = null;

    const startLocalization = async () => {
      try {
        const response = await axios.post('http://localhost:5000/start_localization');
        if (response.data.status === 'success') {
          isLocalizing.value = true;
          errorMessage.value = '';
          ElMessage.success('声源定位已启动！');

          // 连接 WebSocket
          socket = io('http://localhost:5000');
          socket.on('connect', () => {
            console.log('WebSocket 连接成功');
          });
          socket.on('localization_data', (data) => {
            if (data.waveforms && data.direction !== undefined) {
              micWaveforms.value = data.waveforms;
              sourceDirection.value = data.direction;
              updateWaveforms();
              updatePolarChart(data.direction);
            }
          });
          socket.on('error', (error) => {
            errorMessage.value = `WebSocket 错误: ${error.message}`;
            console.error('WebSocket 错误:', error);
            stopLocalization();
          });
        } else {
          errorMessage.value = '启动声源定位失败';
          console.error('服务器响应:', response.data);
        }
      } catch (error) {
        let errorMsg = '启动声源定位失败';
        if (error.response) {
          errorMsg = `启动声源定位失败: ${error.response.data.error || error.message}`;
        } else if (error.request) {
          errorMsg = '启动声源定位失败: 无法连接到服务器';
        } else {
          errorMsg = `启动声源定位失败: ${error.message}`;
        }
        errorMessage.value = errorMsg;
        console.error('启动声源定位失败:', error);
      }
    };

    const stopLocalization = async () => {
      try {
        const response = await axios.post('http://localhost:5000/stop_localization');
        if (response.data.status === 'success') {
          isLocalizing.value = false;
          micWaveforms.value = [];
          sourceDirection.value = null;
          if (polarChart.value) {
            polarChart.value.destroy();
            polarChart.value = null;
          }
          if (socket) {
            socket.disconnect();
            socket = null;
          }
          ElMessage.success('声源定位已停止！');
          errorMessage.value = '';
        } else {
          errorMessage.value = '停止声源定位失败';
          console.error('服务器响应:', response.data);
        }
      } catch (error) {
        let errorMsg = '停止声源定位失败';
        if (error.response) {
          errorMsg = `停止声源定位失败: ${error.response.data.error || error.message}`;
        } else if (error.request) {
          errorMsg = '停止声源定位失败: 无法连接到服务器';
        } else {
          errorMsg = `停止声源定位失败: ${error.message}`;
        }
        errorMessage.value = errorMsg;
        console.error('停止声源定位失败:', error);
      }
    };

    const updateWaveforms = async () => {
      await nextTick();
      micWaveforms.value.forEach((waveform, index) => {
        const canvas = this.$refs[`micCanvas${index}`];
        if (canvas && waveform && waveform.length) {
          const ctx = canvas.getContext('2d');
          if (!ctx) return;
          ctx.clearRect(0, 0, canvas.width, canvas.height);
          ctx.beginPath();
          ctx.strokeStyle = '#409EFF';
          ctx.lineWidth = 2;

          const width = canvas.width;
          const height = canvas.height;
          const samples = Math.min(waveform.length, 1000);
          const step = waveform.length / samples;

          for (let i = 0; i < samples; i++) {
            const idx = Math.floor(i * step);
            const x = i * (width / samples);
            const y = ((1 - waveform[idx]) * height) / 2;
            if (i === 0) {
              ctx.moveTo(x, y);
            } else {
              ctx.lineTo(x, y);
            }
          }
          ctx.stroke();
        }
      });
    };

    const updatePolarChart = (direction) => {
      if (!polarCanvas.value) return;
      if (polarChart.value) {
        polarChart.value.data.datasets[0].data = [1];
        polarChart.value.data.datasets[0].pointRotation = [direction];
        polarChart.value.update();
        return;
      }

      polarChart.value = new Chart(polarCanvas.value, {
        type: 'polarArea',
        data: {
          datasets: [{
            data: [1],
            backgroundColor: 'rgba(64, 158, 255, 0.5)',
            pointRotation: [direction]
          }]
        },
        options: {
          scales: {
            r: {
              angleLines: { display: true },
              ticks: { display: false },
              min: 0,
              max: 1
            }
          },
          plugins: {
            legend: { display: false }
          }
        }
      });
    };

    return {
      isLocalizing,
      micWaveforms,
      sourceDirection,
      polarCanvas,
      polarChart,
      errorMessage,
      startLocalization,
      stopLocalization
    };
  }
};

const WordSegmentation = {
  template: `
    <div class="word-segmentation">
      <h3>分词识别实验</h3>
      <el-input
        v-model="inputText"
        type="textarea"
        :rows="4"
        placeholder="请输入待分词的中文文本"
        :maxlength="500"
        show-word-limit
      ></el-input>
      <el-button
        type="primary"
        @click="segmentWords"
        :disabled="!inputText.trim() || isProcessing"
      >
        分词
      </el-button>
      <div v-if="wordList.length">
        <h4>分词结果</h4>
        <el-table :data="wordList" style="width: 100%; max-width: 600px">
          <el-table-column prop="index" label="序号" width="100"></el-table-column>
          <el-table-column prop="word" label="词汇"></el-table-column>
        </el-table>
      </div>
      <div v-if="stats">
        <h4>分词统计</h4>
        <p>词汇数量: {{ stats.word_count }}</p>
        <p>平均词长: {{ stats.avg_word_length.toFixed(2) }} 字符</p>
      </div>
      <el-alert v-if="errorMessage" type="error" :title="errorMessage" :closable="false" />
    </div>
  `,
  setup() {
    const inputText = ref('');
    const wordList = ref([]);
    const stats = ref(null);
    const isProcessing = ref(false);
    const errorMessage = ref('');

    const segmentWords = async () => {
      if (!inputText.value.trim()) {
        errorMessage.value = '请输入文本';
        return;
      }
      isProcessing.value = true;
      try {
        const response = await axios.post('http://localhost:5000/word_segmentation', {
          text: inputText.value.trim()
        }, {
          headers: { 'Content-Type': 'application/json' }
        });

        if (response.data.words && response.data.stats) {
          wordList.value = response.data.words.map((word, index) => ({
            index: index + 1,
            word
          }));
          stats.value = response.data.stats;
          errorMessage.value = '';
          ElMessage.success('分词完成！');
        } else {
          errorMessage.value = '服务器未返回有效结果';
          console.error('服务器响应:', response.data);
        }
      } catch (error) {
        let errorMsg = '分词失败';
        if (error.response) {
          errorMsg = `分词失败: ${error.response.data.error || error.message}`;
        } else if (error.request) {
          errorMsg = '分词失败: 无法连接到服务器，请检查后端服务';
        } else {
          errorMsg = `分词失败: ${error.message}`;
        }
        errorMessage.value = errorMsg;
        console.error('分词失败:', error);
      } finally {
        isProcessing.value = false;
      }
    };

    return {
      inputText,
      wordList,
      stats,
      isProcessing,
      errorMessage,
      segmentWords
    };
  }
};

const PosTagging = {
  template: `
    <div class="pos-tagging">
      <h3>词性标注实验</h3>
      <el-input
        v-model="inputText"
        type="textarea"
        :rows="4"
        placeholder="请输入待标注的中文文本"
        :maxlength="500"
        show-word-limit
      ></el-input>
      <el-button
        type="primary"
        @click="posTag"
        :disabled="!inputText.trim() || isProcessing"
      >
        标注
      </el-button>
      <div v-if="posList.length">
        <h4>词性标注结果</h4>
        <el-table :data="posList" style="width: 100%; max-width: 600px">
          <el-table-column prop="index" label="序号" width="100"></el-table-column>
          <el-table-column prop="word" label="词汇"></el-table-column>
          <el-table-column prop="pos" label="词性"></el-table-column>
        </el-table>
      </div>
      <div v-if="stats">
        <h4>词性分布统计</h4>
        <p>词汇数量: {{ stats.word_count }}</p>
        <el-table :data="stats.pos_distribution" style="width: 100%; max-width: 600px">
          <el-table-column prop="pos" label="词性"></el-table-column>
          <el-table-column prop="count" label="数量"></el-table-column>
          <el-table-column prop="percentage" label="比例">
            <template #default="scope">
              {{ (scope.row.percentage * 100).toFixed(2) }}%
            </template>
          </el-table-column>
        </el-table>
      </div>
      <el-alert v-if="errorMessage" type="error" :title="errorMessage" :closable="false" />
    </div>
  `,
  setup() {
    const inputText = ref('');
    const posList = ref([]);
    const stats = ref(null);
    const isProcessing = ref(false);
    const errorMessage = ref('');

    const posTag = async () => {
      if (!inputText.value.trim()) {
        errorMessage.value = '请输入文本';
        return;
      }
      isProcessing.value = true;
      try {
        const response = await axios.post('http://localhost:5000/pos_tagging', {
          text: inputText.value.trim()
        }, {
          headers: { 'Content-Type': 'application/json' }
        });

        if (response.data.pos_tags && response.data.stats) {
          posList.value = response.data.pos_tags.map((item, index) => ({
            index: index + 1,
            word: item.word,
            pos: item.pos
          }));
          stats.value = response.data.stats;
          errorMessage.value = '';
          ElMessage.success('词性标注完成！');
        } else {
          errorMessage.value = '服务器未返回有效结果';
          console.error('服务器响应:', response.data);
        }
      } catch (error) {
        let errorMsg = '词性标注失败';
        if (error.response) {
          errorMsg = `词性标注失败: ${error.response.data.error || error.message}`;
        } else if (error.request) {
          errorMsg = '词性标注失败: 无法连接到服务器，请检查后端服务';
        } else {
          errorMsg = `词性标注失败: ${error.message}`;
        }
        errorMessage.value = errorMsg;
        console.error('词性标注失败:', error);
      } finally {
        isProcessing.value = false;
      }
    };

    return {
      inputText,
      posList,
      stats,
      isProcessing,
      errorMessage,
      posTag
    };
  }
};

const NamedEntityRecognition = {
  template: `
    <div class="named-entity-recognition">
      <h3>命名实体识别实验</h3>
      <el-input
        v-model="inputText"
        type="textarea"
        :rows="4"
        placeholder="请输入待识别的中文文本"
        :maxlength="500"
        show-word-limit
      ></el-input>
      <el-button
        type="primary"
        @click="recognizeEntities"
        :disabled="!inputText.trim() || isProcessing"
      >
        识别
      </el-button>
      <div v-if="entityList.length">
        <h4>命名实体识别结果</h4>
        <el-table :data="entityList" style="width: 100%; max-width: 600px">
          <el-table-column prop="index" label="序号" width="100"></el-table-column>
          <el-table-column prop="entity" label="实体"></el-table-column>
          <el-table-column prop="type" label="类型"></el-table-column>
        </el-table>
      </div>
      <div v-if="stats">
        <h4>实体分布统计</h4>
        <p>实体数量: {{ stats.entity_count }}</p>
        <el-table :data="stats.type_distribution" style="width: 100%; max-width: 600px">
          <el-table-column prop="type" label="类型"></el-table-column>
          <el-table-column prop="count" label="数量"></el-table-column>
          <el-table-column prop="percentage" label="比例">
            <template #default="scope">
              {{ (scope.row.percentage * 100).toFixed(2) }}%
            </template>
          </el-table-column>
        </el-table>
      </div>
      <el-alert v-if="errorMessage" type="error" :title="errorMessage" :closable="false" />
    </div>
  `,
  setup() {
    const inputText = ref('');
    const entityList = ref([]);
    const stats = ref(null);
    const isProcessing = ref(false);
    const errorMessage = ref('');

    const recognizeEntities = async () => {
      if (!inputText.value.trim()) {
        errorMessage.value = '请输入文本';
        return;
      }
      isProcessing.value = true;
      try {
        const response = await axios.post('http://localhost:5000/named_entity_recognition', {
          text: inputText.value.trim()
        }, {
          headers: { 'Content-Type': 'application/json' }
        });

        if (response.data.entities && response.data.stats) {
          entityList.value = response.data.entities.map((item, index) => ({
            index: index + 1,
            entity: item.entity,
            type: item.type
          }));
          stats.value = response.data.stats;
          errorMessage.value = '';
          ElMessage.success('命名实体识别完成！');
        } else {
          errorMessage.value = '服务器未返回有效结果';
          console.error('服务器响应:', response.data);
        }
      } catch (error) {
        let errorMsg = '命名实体识别失败';
        if (error.response) {
          errorMsg = `命名实体识别失败: ${error.response.data.error || error.message}`;
        } else if (error.request) {
          errorMsg = '命名实体识别失败: 无法连接到服务器，请检查后端服务';
        } else {
          errorMsg = `命名实体识别失败: ${error.message}`;
        }
        errorMessage.value = errorMsg;
        console.error('命名实体识别失败:', error);
      } finally {
        isProcessing.value = false;
      }
    };

    return {
      inputText,
      entityList,
      stats,
      isProcessing,
      errorMessage,
      recognizeEntities
    };
  }
};

export default {
  name: 'ExperimentProjectsPage',
  components: {
    SpeechCollection,
    WaveformDisplay,
    SpeechEncoding,
    SamplingFrequency,
    SignalStrength,
    WhiteNoise,
    ShortTimeFourier,
    AutoGainControl,
    EndpointDetection,
    NoiseClassification,
    SpeechEnhancement,
    AddNoise,
    EmotionAnalysis,
    RealTimeLocalization,
    WordSegmentation,
    PosTagging,
    NamedEntityRecognition,
  },
  setup() {
    const experiments = [
      { id: 'speech-collection', name: '语音采集实验', component: SpeechCollection },
      { id: 'waveform-display', name: '语音波形显示实验', component: WaveformDisplay },
      { id: 'speech-encoding', name: '语音编码实验', component: SpeechEncoding },
      { id: 'sampling-frequency', name: '语音采样频率转换实验', component: SamplingFrequency },
      { id: 'signal-strength', name: '语音信号强度实验', component: SignalStrength },
      { id: 'white-noise', name: '白噪音信号实验', component: WhiteNoise },
      { id: 'short-time-fourier', name: '语音短时傅里叶变换实验', component: ShortTimeFourier },
      { id: 'auto-gain-control', name: '音频自动增益频控制实验', component: AutoGainControl },
      { id: 'endpoint-detection', name: '语音端点检测实验', component: EndpointDetection },
      { id: 'noise-classification', name: '语音噪音类实验', component: NoiseClassification },
      { id: 'speech-enhancement', name: '语音增强实验', component: SpeechEnhancement },
      { id: 'add-noise', name: '语音添加噪音实验', component: AddNoise },
      { id: 'emotion-analysis', name: '情感分析实验', component: EmotionAnalysis },
      { id: 'real-time-localization', name: '实时声源定位实验', component: RealTimeLocalization },
      { id: 'word-segmentation', name: '分词识别实验', component: WordSegmentation },
      { id: 'pos-tagging', name: '词性标注实验', component: PosTagging },
      { id: 'named-entity-recognition', name: '命名实体识别实验', component: NamedEntityRecognition },
    ];

    const activeExperiment = ref('speech-collection');

    const handleExperimentSelect = (index) => {
      activeExperiment.value = index;
    };

    const currentExperimentComponent = computed(() => {
      const experiment = experiments.find((exp) => exp.id === activeExperiment.value);
      return experiment ? experiment.component : SpeechCollection;
    });

    const currentExperimentName = computed(() => {
      const experiment = experiments.find((exp) => exp.id === activeExperiment.value);
      return experiment ? experiment.name : '实验项目';
    });

    return {
      experiments,
      activeExperiment,
      handleExperimentSelect,
      currentExperimentComponent,
      currentExperimentName,
    };
  },
};
</script>

<style scoped>
.experiment-projects {
  height: 100%;
}
.experiment-sidebar {
  background-color: #f5f5f5;
  border-right: 1px solid #e6e6e6;
}
.experiment-menu {
  background-color: transparent;
}
.experiment-content {
  padding: 20px;
  min-height: 300px;
  display: flex;
  flex-direction: column;
  align-items: center;
}
.experiment-content h2 {
  margin-top: 0;
}
.named-entity-recognition {
  text-align: center;
  width: 100%;
}
.named-entity-recognition .el-input, .named-entity-recognition .el-button {
  margin: 10px;
}
.named-entity-recognition .el-table, .named-entity-recognition p {
  margin: 10px auto;
  max-width: 600px;
}
.named-entity-recognition .el-alert {
  margin-top: 10px;
  max-width: 600px;
}
</style>