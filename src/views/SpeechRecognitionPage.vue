<!-- src/views/SpeechRecognition.vue -->
<template>
  <div>
    <h2>语音识别</h2>
    <el-row :gutter="20">
      <el-col :span="12">
        <el-form label-width="100px">
          <el-form-item label="选择模型">
            <el-select v-model="selectedModel" placeholder="请选择模型" @change="loadSelectedModel">
              <el-option v-for="model in models" :key="model" :label="model" :value="model"></el-option>
            </el-select>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" :disabled="!selectedModel || isRecognizing" @click="startRecognition">开始识别</el-button>
            <el-button type="danger" :disabled="!isRecognizing" @click="stopRecognition">停止识别</el-button>
          </el-form-item>
        </el-form>
      </el-col>
    </el-row>
    <el-divider></el-divider>
    <el-row>
      <el-col :span="24">
        <h3>识别结果</h3>
        <el-input
          type="textarea"
          v-model="recognitionResult"
          :rows="5"
          placeholder="实时识别结果将显示在这里"
          readonly
        ></el-input>
      </el-col>
    </el-row>
    <el-row v-if="errorMessage">
      <el-col :span="24">
        <el-alert :title="errorMessage" type="error" show-icon></el-alert>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue';
import { ElMessage } from 'element-plus';
import { getModels, loadModel } from '../api'; // 从 api/index.js 导入
import { getCurrentInstance } from 'vue';

// 状态管理
const models = ref([]);
const selectedModel = ref('');
const isRecognizing = ref(false);
const recognitionResult = ref('');
const errorMessage = ref('');
const socket = getCurrentInstance().appContext.config.globalProperties.$socket;

// Web Audio API 相关
let mediaStream = null;
let audioContext = null;
let sourceNode = null;
let processorNode = null;

// 获取可用模型
const fetchModels = async () => {
  try {
    const response = await getModels();
    models.value = response.data;
    if (models.value.length > 0) {
      selectedModel.value = models.value[0]; // 默认选择第一个模型
      loadSelectedModel(selectedModel.value);
    }
  } catch (error) {
    ElMessage.error('获取模型列表失败');
  }
};

// 加载选定模型
const loadSelectedModel = async (model) => {
  try {
    const response = await loadModel(model);
    if (response.data.status === 'success') {
      ElMessage.success('模型加载成功');
    } else {
      ElMessage.error(response.data.message || '模型加载失败');
    }
  } catch (error) {
    ElMessage.error('模型加载失败');
  }
};

// 启动麦克风录制
const startRecording = async () => {
  try {
    mediaStream = await navigator.mediaDevices.getUserMedia({ audio: true });
    audioContext = new (window.AudioContext || window.webkitAudioContext)();
    sourceNode = audioContext.createMediaStreamSource(mediaStream);
    processorNode = audioContext.createScriptProcessor(4096, 1, 1);

    processorNode.onaudioprocess = (e) => {
      if (isRecognizing.value) {
        const audioData = e.inputBuffer.getChannelData(0);
        socket.emit('audio_data', Array.from(audioData));
      }
    };

    sourceNode.connect(processorNode);
    processorNode.connect(audioContext.destination);
  } catch (error) {
    ElMessage.error('无法访问麦克风：' + error.message);
    isRecognizing.value = false;
  }
};

// 停止麦克风录制
const stopRecording = () => {
  if (processorNode) {
    processorNode.disconnect();
    processorNode = null;
  }
  if (sourceNode) {
    sourceNode.disconnect();
    sourceNode = null;
  }
  if (audioContext) {
    audioContext.close();
    audioContext = null;
  }
  if (mediaStream) {
    mediaStream.getTracks().forEach(track => track.stop());
    mediaStream = null;
  }
};

// 启动实时识别
const startRecognition = () => {
  if (!selectedModel.value) {
    ElMessage.error('请先选择模型');
    return;
  }
  socket.emit('start_recognition_process', { model: selectedModel.value });
  startRecording();
};

// 停止实时识别
const stopRecognition = () => {
  socket.emit('stop_recognition');
  stopRecording();
};

// WebSocket 事件监听
socket.on('recognition_result', (data) => {
  if (data.text) {
    recognitionResult.value += (recognitionResult.value ? '\n' : '') + data.text;
    isRecognizing.value = true;
  } else if (data.error) {
    errorMessage.value = data.error;
    ElMessage.error(data.error);
    isRecognizing.value = false;
    stopRecording();
  } else if (data.text === '实时识别已停止' || data.text === '实时识别强制终止') {
    isRecognizing.value = false;
    stopRecording();
    ElMessage.info(data.text);
  }
});

// 组件生命周期
onMounted(() => {
  fetchModels();
});

onUnmounted(() => {
  stopRecognition();
});
</script>

<style scoped>
.el-row {
  margin-bottom: 20px;
}
.el-divider {
  margin: 20px 0;
}
</style>