<!-- src/views/VoiceClone.vue -->
<template>
  <div>
    <h2>语音克隆</h2>
    <el-row :gutter="20">
      <el-col :span="12">
        <el-form label-width="120px">
          <el-form-item label="选择模型">
            <el-select v-model="selectedModel" placeholder="请选择模型" :disabled="isCloning">
              <el-option v-for="model in models" :key="model" :label="model" :value="model"></el-option>
            </el-select>
          </el-form-item>
          <el-form-item label="上传音频">
            <el-upload
              action="#"
              :http-request="handleAudioUpload"
              :show-file-list="false"
              accept=".wav,.mp3"
              :disabled="!selectedModel || isCloning"
            >
              <el-button type="primary">选择克隆音频 (.wav 或 .mp3)</el-button>
            </el-upload>
            <p v-if="audioPath">音频路径：{{ audioPath }}</p>
          </el-form-item>
          <el-form-item label="合成文本">
            <el-input v-model="synthText" placeholder="请输入要合成的文本" :disabled="isCloning"></el-input>
          </el-form-item>
          <el-form-item label="语言提示">
            <el-select v-model="langTip" placeholder="选择语言" :disabled="isCloning">
              <el-option label="中文" value="zh"></el-option>
              <el-option label="英文" value="en"></el-option>
              <!-- 添加更多语言根据需要 -->
            </el-select>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" :disabled="!selectedModel || !audioPath || !synthText || isCloning" @click="startClone">开始克隆</el-button>
          </el-form-item>
        </el-form>
      </el-col>
    </el-row>
    <el-divider></el-divider>
    <el-row>
      <el-col :span="24">
        <h3>克隆结果</h3>
        <audio v-if="audioUrl" :src="audioUrl" controls autoplay></audio>
        <p v-if="cloneStatus">{{ cloneStatus }}</p>
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
import { ElMessage, ElLoading } from 'element-plus';
import { listVoiceModels, uploadCloneAudio } from '../api';
import { getCurrentInstance } from 'vue';

const models = ref([]);
const selectedModel = ref('');
const audioPath = ref('');
const synthText = ref('');
const langTip = ref('zh');
const audioUrl = ref('');
const cloneStatus = ref('');
const errorMessage = ref('');
const isCloning = ref(false);
const socket = getCurrentInstance().appContext.config.globalProperties.$socket;

// 获取语音模型列表
const fetchModels = async () => {
  try {
    const response = await listVoiceModels();
    models.value = response.data;
    if (models.value.length > 0) {
      selectedModel.value = models.value[0];
    }
  } catch (error) {
    ElMessage.error('获取模型列表失败');
  }
};

// 处理音频上传
const handleAudioUpload = async (file) => {
  const loading = ElLoading.service({ text: '上传音频...' });
  try {
    const formData = new FormData();
    formData.append('clone_audio', file.file);
    const response = await uploadCloneAudio(formData);
    audioPath.value = response.data.path;
    ElMessage.success('音频上传成功');
  } catch (error) {
    errorMessage.value = error.response?.data?.error || '音频上传失败';
    ElMessage.error(errorMessage.value);
  } finally {
    loading.close();
  }
};

// 开始语音克隆
const startClone = () => {
  if (!selectedModel.value || !audioPath.value || !synthText.value) {
    ElMessage.error('缺少模型、音频或文本');
    return;
  }
  isCloning.value = true;
  cloneStatus.value = '开始语音克隆...';
  socket.emit('start_clone', {
    model_path: selectedModel.value,
    audio_path: audioPath.value,
    synth_text: synthText.value,
    lang_tip: langTip.value
  });
};

// 监听 WebSocket 事件
socket.on('clone_result', (data) => {
  if (data.text) {
    cloneStatus.value = data.text;
    if (data.audio_path) {
      audioUrl.value = `http://localhost:5000/audio/${data.audio_path}`;
      ElMessage.success('语音克隆完成');
      isCloning.value = false;
    }
  } else if (data.error) {
    errorMessage.value = data.error;
    ElMessage.error(data.error);
    isCloning.value = false;
  }
});

// 组件生命周期
onMounted(() => {
  fetchModels();
});

onUnmounted(() => {
  // 可选：如果需要停止克隆
});
</script>

<style scoped>
.el-row {
  margin-bottom: 20px;
}
.el-divider {
  margin: 20px 0;
}
audio {
  margin-top: 10px;
}
</style>