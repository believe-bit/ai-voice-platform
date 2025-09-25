<!-- src/views/OfflineAudioRecognition.vue -->
<template>
  <div>
    <h2>离线音频文件识别</h2>
    <el-row :gutter="20">
      <el-col :span="12">
        <el-form label-width="100px">
          <el-form-item label="选择模型">
            <el-select v-model="selectedModel" placeholder="请选择模型" :disabled="isRecognizing">
              <el-option v-for="model in models" :key="model" :label="model" :value="model"></el-option>
            </el-select>
          </el-form-item>
          <el-form-item label="上传音频">
            <el-upload
              action="#"
              :http-request="handleUpload"
              :show-file-list="false"
              accept=".wav"
              :disabled="!selectedModel || isRecognizing"
              :before-upload="beforeUpload"
            >
              <el-button type="primary">选择音频文件 (.wav)</el-button>
            </el-upload>
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
          placeholder="音频识别结果将显示在这里"
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
import { ref, onMounted } from 'vue';
import { ElMessage, ElLoading } from 'element-plus';
import { getModels, recognizeAudio } from '../api'; // 确保导入 recognizeAudio

// 状态管理
const models = ref([]);
const selectedModel = ref('');
const recognitionResult = ref('');
const errorMessage = ref('');
const isRecognizing = ref(false);

// 获取可用模型
const fetchModels = async () => {
  try {
    const response = await getModels();
    models.value = response.data;
    if (models.value.length > 0) {
      selectedModel.value = models.value[0]; // 默认选择第一个模型
    } else {
      errorMessage.value = '没有可用的模型';
      ElMessage.error('没有可用的模型');
    }
  } catch (error) {
    errorMessage.value = '获取模型列表失败：' + (error.message || '未知错误');
    ElMessage.error(errorMessage.value);
  }
};

// 文件上传前检查
const beforeUpload = (file) => {
  const maxSize = 10 * 1024 * 1024; // 10MB
  if (file.size > maxSize) {
    ElMessage.error('文件大小不能超过10MB');
    return false;
  }
  if (!file.name.endsWith('.wav')) {
    ElMessage.error('仅支持 .wav 文件');
    return false;
  }
  return true;
};

// 处理音频文件上传和识别
const handleUpload = async (file) => {
  if (!selectedModel.value) {
    ElMessage.error('请先选择模型');
    return;
  }

  const loading = ElLoading.service({
    lock: true,
    text: '正在识别音频...',
    background: 'rgba(0, 0, 0, 0.7)',
  });

  try {
    isRecognizing.value = true;
    const formData = new FormData();
    formData.append('audio', file.file);
    formData.append('model', selectedModel.value);

    console.log('发送请求到 /recognize', { model: selectedModel.value, file: file.file.name }); // 调试日志
    const response = await recognizeAudio(formData);
    console.log('识别结果：', response.data); // 调试日志

    if (response.data.text) {
      recognitionResult.value = response.data.text;
      ElMessage.success('音频识别成功');
    } else {
      recognitionResult.value = '无识别结果';
      ElMessage.warning('未识别到有效文本');
    }
  } catch (error) {
    console.error('识别错误：', error); // 调试日志
    errorMessage.value = error.response?.data?.error || `音频识别失败：${error.message || '未知错误'}`;
    ElMessage.error(errorMessage.value);
  } finally {
    isRecognizing.value = false;
    loading.close();
  }
};

// 组件生命周期
onMounted(() => {
  fetchModels();
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