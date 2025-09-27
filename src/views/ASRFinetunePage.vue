<!-- src/views/ASRFinetune.vue -->
<template>
  <div>
    <h2>ASR模型微调</h2>
    <el-row :gutter="20">
      <el-col :span="12">
        <el-form label-width="120px">
          <el-form-item label="选择模型">
            <el-select v-model="selectedModel" placeholder="请选择模型" :disabled="isTraining">
              <el-option v-for="model in models" :key="model" :label="model" :value="model"></el-option>
            </el-select>
          </el-form-item>
          <el-form-item label="上传数据集">
            <el-upload
              action="#"
              :http-request="handleDatasetUpload"
              :show-file-list="false"
              accept=".zip"
              :disabled="!selectedModel || isTraining"
            >
              <el-button type="primary">选择 ZIP 数据集</el-button>
            </el-upload>
            <p v-if="datasetPath">数据集路径：{{ datasetPath }} (有效样本：{{ validSamples }})</p>
          </el-form-item>
          <el-form-item label="训练轮次">
            <el-input-number v-model="trainingParams.per_device_train_batch_size" label="Batch Size" :min="1" :disabled="isTraining"></el-input-number>
          </el-form-item>
          <el-form-item label="训练批次">
            <el-input-number v-model="trainingParams.gradient_accumulation_steps" label="Gradient Steps" :min="1" :disabled="isTraining"></el-input-number>
          </el-form-item>
          <el-form-item label="迭代次数">
            <el-input-number v-model="trainingParams.num_train_epochs" label="Epochs" :min="1" :disabled="isTraining"></el-input-number>
          </el-form-item>
          <el-form-item label="学习率">
            <el-input v-model="trainingParams.learning_rate" placeholder="Learning Rate (e.g., 1e-5)" :disabled="isTraining"></el-input>
          </el-form-item>
          <el-form-item label="启用GPU">
            <el-switch v-model="trainingParams.fp16" active-text="" :disabled="isTraining"></el-switch>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" :disabled="!datasetPath || isTraining" @click="startTrain">开始训练</el-button>
            <el-button type="danger" :disabled="!isTraining" @click="stopTrain">停止训练</el-button>
          </el-form-item>
        </el-form>
      </el-col>
    </el-row>
    <el-divider></el-divider>
    <el-row>
      <el-col :span="24">
        <h3>训练日志</h3>
        <el-input
          type="textarea"
          v-model="trainingLogs"
          :rows="10"
          placeholder="训练日志将实时显示在这里"
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
import { ElMessage, ElLoading } from 'element-plus';
import { listModels, uploadDataset, startAsrTrain, stopAsrTrain, getStreamLogs } from '../api';  // 更新导入

// 状态管理
const models = ref([]);
const selectedModel = ref('');
const datasetPath = ref('');
const validSamples = ref(0);
const trainingParams = ref({
  per_device_train_batch_size: 2,
  gradient_accumulation_steps: 1,
  num_train_epochs: 1,
  learning_rate: '1e-5',
  fp16: false
});
const trainingLogs = ref('');
const errorMessage = ref('');
const isTraining = ref(false);
let eventSource = null;

// 获取 ASR 模型列表
const fetchModels = async () => {
  try {
    const response = await listModels('asr-finetune');
    if (response && response.data) {
      models.value = response.data;
      if (models.value.length > 0) {
        selectedModel.value = models.value[0];
      }
    } else {
      console.error('获取模型列表失败: 返回数据格式不正确');
      ElMessage.error('获取模型列表失败: 返回数据格式不正确');
    }
  } catch (error) {
    console.error('获取模型列表失败:', error);
    ElMessage.error(`获取模型列表失败: ${error.message || '未知错误'}`);
  }
};

// 处理数据集上传
const handleDatasetUpload = async (file) => {
  const loading = ElLoading.service({ text: '上传并解压数据集...' });
  try {
    const formData = new FormData();
    formData.append('file', file.file);
    const response = await uploadDataset(formData);
    datasetPath.value = response.data.dataset_path;
    validSamples.value = response.data.valid_samples;
    ElMessage.success('数据集上传成功');
  } catch (error) {
    errorMessage.value = error.response?.data?.error || '数据集上传失败';
    ElMessage.error(errorMessage.value);
  } finally {
    loading.close();
  }
};

// 开始训练
const startTrain = async () => {
  if (!selectedModel.value || !datasetPath.value) {
    ElMessage.error('请先选择模型并上传数据集');
    return;
  }
  const loading = ElLoading.service({ text: '启动训练...' });
  try {
    isTraining.value = true;
    trainingLogs.value = ''; // 清空日志
    const data = {
      model: selectedModel.value,
      dataset_path: datasetPath.value,
      training_params: trainingParams.value
    };
    console.log('开始训练请求：', data);
    const response = await startAsrTrain(data);  // 更新为 startAsrTrain
    console.log('训练启动响应：', response.data);
    ElMessage.success('训练已开始');
    startLogStream();
  } catch (error) {
    console.error('训练启动错误:', error, '响应:', error.response?.data);
    errorMessage.value = error.response?.data?.error || '启动训练失败';
    ElMessage.error(errorMessage.value);
    isTraining.value = false;
  } finally {
    loading.close();
  }
};

// 停止训练
const stopTrain = async () => {
  const loading = ElLoading.service({ text: '停止训练...' });
  try {
    await stopAsrTrain();  // 更新为 stopAsrTrain
    ElMessage.success('训练已停止');
    isTraining.value = false;
    stopLogStream();
  } catch (error) {
    errorMessage.value = error.response?.data?.error || '停止训练失败';
    ElMessage.error(errorMessage.value);
  } finally {
    loading.close();
  }
};

// 启动日志流
const startLogStream = () => {
  const url = getStreamLogs();
  console.log('启动日志流:', url);
  eventSource = new EventSource(url);
  eventSource.onmessage = (event) => {
    console.log('收到日志:', event.data);
    trainingLogs.value += (trainingLogs.value ? '\n' : '') + event.data;
    if (event.data === '[训练完成]' || event.data === '[训练已停止]') {
      isTraining.value = false;
      stopLogStream();
    }
  };
  eventSource.onerror = (error) => {
    console.error('日志流错误：', error);
    ElMessage.error('日志流连接失败');
    stopLogStream();
  };
};

// 停止日志流
const stopLogStream = () => {
  if (eventSource) {
    console.log('停止日志流');
    eventSource.close();
    eventSource = null;
  }
};

// 组件生命周期
onMounted(() => {
  fetchModels();
});

onUnmounted(() => {
  stopLogStream();
});
</script>