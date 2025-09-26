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
          <el-form-item label="语速">
            <el-input-number v-model="params.speech_rate" label="语速" :min="0.5" :max="2.0" :step="0.1" :disabled="isSynthesizing"></el-input-number>
          </el-form-item>
          <el-form-item label="音量">
            <el-input-number v-model="params.volume" label="音量" :min="0.5" :max="2.0" :step="0.1" :disabled="isSynthesizing"></el-input-number>
          </el-form-item>
          <el-form-item label="音调">
            <el-select v-model="params.pitch" placeholder="音调" :disabled="isSynthesizing">
              <el-option label="normal" value="normal"></el-option>
              <el-option label="high" value="high"></el-option>
              <el-option label="low" value="low"></el-option>
            </el-select>
          </el-form-item>
          <el-form-item label="情感语气">
            <el-select v-model="params.emotion_tone" placeholder="情感语气" :disabled="isSynthesizing">
              <el-option label="calm" value="calm"></el-option>
              <el-option label="happy" value="happy"></el-option>
              <el-option label="sad" value="sad"></el-option>
            </el-select>
          </el-form-item>
          <el-form-item label="音色">
            <el-select v-model="params.voice" placeholder="声音" :disabled="isSynthesizing">
              <el-option label="zhiyan_emo" value="zhiyan_emo"></el-option>
              <el-option label="zhibei_emo" value="zhibei_emo"></el-option>
              <el-option label="zhitian_emo" value="zhitian_emo"></el-option>
              <el-option label="zhizhe_emo" value="zhizhe_emo"></el-option>
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

const stopTTS = () => {
  socket.emit('stop_tts');
  isSynthesizing.value = false;
  synthesisStatus.value = '语音合成已停止';
};

socket.on('tts_result', (data) => {
  console.log('收到 tts_result:', data);
  if (data.text) {
    synthesisStatus.value = data.text;
    if (data.audio && data.text.includes('音频已保存到')) {
      audioUrl.value = `http://localhost:5000/audio/${data.audio}`;
      // 验证音频文件是否可访问
      fetch(audioUrl.value)
        .then(response => {
          if (response.ok) {
            ElMessage.success('语音合成完成');
            isSynthesizing.value = false;
            // 自动播放音频
            const audio = new Audio(audioUrl.value);
            audio.play().catch(err => {
              console.error('音频播放失败:', err);
              ElMessage.error('音频播放失败: ' + err.message);
            });
          } else {
            ElMessage.error('无法访问音频文件');
            isSynthesizing.value = false;
          }
        })
        .catch(err => {
          console.error('音频请求失败:', err);
          ElMessage.error('音频请求失败: ' + err.message);
          isSynthesizing.value = false;
        });
    }
  } else if (data.error) {
    errorMessage.value = data.error;
    ElMessage.error(data.error);
    isSynthesizing.value = false;
  }
});

onMounted(() => {
  fetchModels();
});

onUnmounted(() => {
  if (isSynthesizing.value) {
    stopTTS();
  }
});
</script>