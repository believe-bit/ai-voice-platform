<!-- src/views/SpeechSynthesis.vue -->
<template>
  <div>
    <h2>语音合成</h2>
    <el-row :gutter="20">
      <el-col :span="12">
        <el-form label-width="120px">
          <el-form-item label="选择模型">
            <el-select v-model="selectedModel" placeholder="请选择模型" :disabled="isSynthesizing">
              <el-option v-for="model in models" :key="model" :label="model" :value="model"></el-option>
            </el-select>
          </el-form-item>
          <el-form-item label="输入文本">
            <el-input v-model="text" placeholder="请输入要合成的文本" :disabled="isSynthesizing"></el-input>
          </el-form-item>
          <el-form-item label="合成参数">
            <el-input-number v-model="params.speech_rate" label="语速" :min="0.5" :max="2.0" :step="0.1" :disabled="isSynthesizing"></el-input-number>
            <el-input-number v-model="params.volume" label="音量" :min="0.5" :max="2.0" :step="0.1" :disabled="isSynthesizing"></el-input-number>
            <el-select v-model="params.pitch" placeholder="音调" :disabled="isSynthesizing">
              <el-option label="normal" value="normal"></el-option>
              <el-option label="high" value="high"></el-option>
              <el-option label="low" value="low"></el-option>
            </el-select>
            <el-select v-model="params.emotion_tone" placeholder="情感语气" :disabled="isSynthesizing">
              <el-option label="calm" value="calm"></el-option>
              <el-option label="happy" value="happy"></el-option>
              <el-option label="sad" value="sad"></el-option>
            </el-select>
            <el-select v-model="params.voice" placeholder="声音" :disabled="isSynthesizing">
              <el-option label="zhiyan_emo" value="zhiyan_emo"></el-option>
              <!-- 添加更多声音选项根据需要 -->
            </el-select>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" :disabled="!selectedModel || !text || isSynthesizing" @click="startTTS">开始合成</el-button>
            <el-button type="danger" :disabled="!isSynthesizing" @click="stopTTS">停止合成</el-button>
          </el-form-item>
        </el-form>
      </el-col>
    </el-row>
    <el-divider></el-divider>
    <el-row>
      <el-col :span="24">
        <h3>合成结果</h3>
        <audio v-if="audioUrl" :src="audioUrl" controls autoplay></audio>
        <p v-if="synthesisStatus">{{ synthesisStatus }}</p>
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
import { listModels } from '../api';
import { getCurrentInstance } from 'vue';

const models = ref([]);
const selectedModel = ref('');
const text = ref('');
const params = ref({
  speech_rate: 1.0,
  volume: 1.0,
  pitch: 'normal',
  emotion_tone: 'calm',
  voice: 'zhiyan_emo'
});
const audioUrl = ref('');
const synthesisStatus = ref('');
const errorMessage = ref('');
const isSynthesizing = ref(false);
const socket = getCurrentInstance().appContext.config.globalProperties.$socket;

// 获取 TTS 模型列表
const fetchModels = async () => {
  try {
    const response = await listModels('tts');
    models.value = response.data;
    if (models.value.length > 0) {
      selectedModel.value = models.value[0];
    }
  } catch (error) {
    ElMessage.error('获取模型列表失败');
  }
};

// 开始语音合成
const startTTS = () => {
  if (!selectedModel.value || !text.value) {
    ElMessage.error('缺少模型或文本');
    return;
  }
  isSynthesizing.value = true;
  synthesisStatus.value = '开始语音合成...';
  socket.emit('start_tts', {
    model: selectedModel.value,
    text: text.value,
    params: params.value
  });
};

// 停止语音合成
const stopTTS = () => {
  socket.emit('stop_tts');
  isSynthesizing.value = false;
  synthesisStatus.value = '语音合成已停止';
};

// 监听 WebSocket 事件
socket.on('tts_result', (data) => {
  if (data.text) {
    synthesisStatus.value = data.text;
    if (data.audio) {
      audioUrl.value = `http://localhost:5000/audio/${data.audio}`;
      ElMessage.success('语音合成完成');
    }
  } else if (data.error) {
    errorMessage.value = data.error;
    ElMessage.error(data.error);
    isSynthesizing.value = false;
  }
});

// 组件生命周期
onMounted(() => {
  fetchModels();
});

onUnmounted(() => {
  if (isSynthesizing.value) {
    stopTTS();
  }
});
</script>

<style scoped>
.el-row {
  margin-bottom: 20px;
}
.el-divider {
  margin: 20px 0;
}
.el-input-number, .el-select {
  margin-right: 10px;
  margin-bottom: 10px;
}
audio {
  margin-top: 10px;
}
</style>