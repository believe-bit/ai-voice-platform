<!-- src/views/VITSTrain.vue -->
<template>
  <div>
    <h2>VITS模型训练</h2>
    <el-tabs v-model="activeTab" type="card">
      <el-tab-pane label="模型训练" name="train">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form label-width="120px">
              <el-form-item label="上传数据集">
                <el-upload
                  action="#"
                  :http-request="handleDatasetUpload"
                  :show-file-list="false"
                  accept=".zip"
                  :disabled="isTraining"
                >
                  <el-button type="primary">选择 ZIP 数据集</el-button>
                </el-upload>
                <p v-if="datasetPath">数据集路径：{{ datasetPath }} (有效样本：{{ validSamples }})</p>
              </el-form-item>
              <el-form-item label="模型名称">
                <el-input v-model="modelName" placeholder="输入模型名称" :disabled="isTraining"></el-input>
              </el-form-item>
              <el-form-item label="训练参数">
                <el-input-number v-model="trainingParams.epochs" label="Epochs" :min="1" :disabled="isTraining"></el-input-number>
                <el-input-number v-model="trainingParams.batch_size" label="Batch Size" :min="1" :disabled="isTraining"></el-input-number>
                <el-input v-model="trainingParams.lr" placeholder="Learning Rate (e.g., 1e-5)" :disabled="isTraining"></el-input>
                <el-switch v-model="trainingParams.use_gpu" active-text="使用 GPU" :disabled="isTraining"></el-switch>
              </el-form-item>
              <el-form-item>
                <el-button type="primary" :disabled="!datasetPath || !modelName || isTraining" @click="startTrain">开始训练</el-button>
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
      </el-tab-pane>
      <el-tab-pane label="模型测试" name="test">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form label-width="120px">
              <el-form-item label="选择模型">
                <el-select v-model="selectedModel" placeholder="请选择模型" :disabled="isTesting">
                  <el-option v-for="model in trainedModels" :key="model" :label="model" :value="model"></el-option>
                </el-select>
              </el-form-item>
              <el-form-item label="输入文本">
                <el-input v-model="testText" placeholder="请输入要测试的文本" :disabled="isTesting"></el-input>
              </el-form-item>
              <el-form-item label="测试参数">
                <el-input-number v-model="testParams.speech_rate" label="语速" :min="0.5" :max="2.0" :step="0.1" :disabled="isTesting"></el-input-number>
                <el-input-number v-model="testParams.volume" label="音量" :min="0.5" :max="2.0" :step="0.1" :disabled="isTesting"></el-input-number>
              </el-form-item>
              <el-form-item>
                <el-button type="primary" :disabled="!selectedModel || !testText || isTesting" @click="startTest">开始测试</el-button>
              </el-form-item>
            </el-form>
          </el-col>
        </el-row>
        <el-divider></el-divider>
        <el-row>
          <el-col :span="24">
            <audio v-if="audioUrl" :src="audioUrl" controls autoplay @error="handleAudioError"></audio>
            <p v-if="testStatus">{{ testStatus }}</p>
            <el-input
              type="textarea"
              v-model="testLogs"
              :rows="10"
              placeholder="测试日志将实时显示在这里"
              readonly
            ></el-input>
          </el-col>
        </el-row>
      </el-tab-pane>
    </el-tabs>
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
import { listModels, uploadDataset, startVitsTrain, stopVitsTrain, vitsTest } from '../api';

// 训练面板状态
const activeTab = ref('train');
const datasetPath = ref('');
const validSamples = ref(0);
const modelName = ref('default_model');
const trainingParams = ref({
  epochs: 20,
  batch_size: 16,
  lr: '1e-5',
  use_gpu: false
});
const trainingLogs = ref('');
const isTraining = ref(false);
const errorMessage = ref('');
let trainEventSource = null;

// 测试面板状态
const trainedModels = ref([]);
const selectedModel = ref('');
const testText = ref('');
const testParams = ref({
  speech_rate: 1.0,
  volume: 1.0
});
const audioUrl = ref('');
const testStatus = ref('');
const testLogs = ref('');
const isTesting = ref(false);
let testEventSource = null;


// 训练面板：上传数据集
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

// 训练面板：开始训练
const startTrain = async () => {
  if (!datasetPath.value || !modelName.value) {
    ElMessage.error('请先上传数据集并输入模型名称');
    return;
  }
  const loading = ElLoading.service({ text: '启动训练...' });
  try {
    isTraining.value = true;
    trainingLogs.value = '';
    const data = {
      dataset_path: datasetPath.value,
      epochs: trainingParams.value.epochs,
      batch_size: trainingParams.value.batch_size,
      lr: trainingParams.value.lr,
      use_gpu: trainingParams.value.use_gpu,
      model_name: modelName.value
    };
    console.log('开始训练请求：', data);
    const response = await startVitsTrain(data);
    console.log('训练启动响应：', response.data);
    ElMessage.success('训练已开始');
    startTrainLogStream();
  } catch (error) {
    errorMessage.value = error.response?.data?.error || '启动训练失败';
    ElMessage.error(errorMessage.value);
    isTraining.value = false;
  } finally {
    loading.close();
  }
};

// 训练面板：停止训练
const stopTrain = async () => {
  const loading = ElLoading.service({ text: '停止训练...' });
  try {
    await stopVitsTrain();
    ElMessage.success('训练已停止');
    isTraining.value = false;
    stopTrainLogStream();
  } catch (error) {
    errorMessage.value = error.response?.data?.error || '停止训练失败';
    ElMessage.error(errorMessage.value);
  } finally {
    loading.close();
  }
};

// 训练面板：启动日志流
const startTrainLogStream = () => {
  const url = 'http://localhost:5000/vits_train_log';
  trainEventSource = new EventSource(url);
  trainEventSource.onmessage = (event) => {
    trainingLogs.value += (trainingLogs.value ? '\n' : '') + event.data;
    if (event.data === '[训练完成]' || event.data === '[训练已停止]') {
      isTraining.value = false;
      stopTrainLogStream();
    }
  };
  trainEventSource.onerror = (error) => {
    console.error('训练日志流错误：', error);
    ElMessage.error('训练日志流连接失败');
    stopTrainLogStream();
  };
};

// 训练面板：停止日志流
const stopTrainLogStream = () => {
  if (trainEventSource) {
    trainEventSource.close();
    trainEventSource = null;
  }
};

// 测试面板：获取训练模型列表
const fetchTrainedModels = async () => {
  try {
    const response = await listModels('vits');
    console.log('训练模型列表：', response.data);
    if (response.data.error) {
      throw new Error(response.data.error);
    }
    trainedModels.value = response.data;
    if (trainedModels.value.length > 0) {
      selectedModel.value = trainedModels.value[0];
    } else {
      errorMessage.value = '暂无训练模型，请先完成训练';
      ElMessage.warning(errorMessage.value);
    }
  } catch (error) {
    console.error('获取训练模型列表失败：', error);
    errorMessage.value = `获取训练模型列表失败：${error.message || error}`;
    ElMessage.error(errorMessage.value);
  }
};

// 测试面板：开始测试
const startTest = async () => {
  if (!selectedModel.value || !testText.value) {
    ElMessage.error('缺少模型或文本');
    return;
  }
  const loading = ElLoading.service({ text: '启动测试...' });
  try {
    isTesting.value = true;
    testLogs.value = '';
    audioUrl.value = '';
    const data = {
      model_name: selectedModel.value,
      text: testText.value,
      speech_rate: testParams.value.speech_rate,
      volume: testParams.value.volume
    };
    console.log('开始测试请求：', data);
    const response = await vitsTest(data);
    console.log('测试响应：', response.data);
    testStatus.value = '测试完成';
    audioUrl.value = `http://localhost:5000/audio/${response.data.audio_path}`;
    ElMessage.success('测试已完成');
    startTestLogStream();
  } catch (error) {
    errorMessage.value = error.response?.data?.error || '测试失败';
    ElMessage.error(errorMessage.value);
    isTesting.value = false;
  } finally {
    loading.close();
  }
};

// 测试面板：启动日志流
const startTestLogStream = () => {
  const url = 'http://localhost:5000/vits_test_log';
  console.log('尝试连接测试日志流:', url);
  testEventSource = new EventSource(url);
  testEventSource.onopen = () => {
    console.log('测试日志流连接成功');
  };
  testEventSource.onmessage = (event) => {
    console.log('收到测试日志:', event.data);
    testLogs.value += (testLogs.value ? '\n' : '') + event.data;
    if (event.data === '[测试完成]') {
      isTesting.value = false;
      stopTestLogStream();
    }
  };
  testEventSource.onerror = (error) => {
    console.error('测试日志流错误:', error);
    // 忽略因正常关闭触发的错误
    if (!isTesting.value) {
      console.log('日志流因测试完成关闭，忽略错误');
      return;
    }
    ElMessage.error('测试日志流连接失败，尝试重连...');
    stopTestLogStream();
    setTimeout(() => {
      if (!testEventSource && isTesting.value) {
        console.log('重试测试日志流连接');
        startTestLogStream();
      }
    }, 2000);
  };
};

// 测试面板：停止日志流
const stopTestLogStream = () => {
  if (testEventSource) {
    console.log('关闭测试日志流');
    testEventSource.close();
    testEventSource = null;
  }
};

// 组件生命周期
onMounted(() => {
  fetchTrainedModels();
});

onUnmounted(() => {
  stopTrainLogStream();
  stopTestLogStream();
});
</script>

<style scoped>
.el-row {
  margin-bottom: 20px;
}
.el-divider {
  margin: 20px 0;
}
.el-input-number,
.el-input,
.el-switch {
  margin-right: 10px;
  margin-bottom: 10px;
}
audio {
  margin-top: 10px;
}
</style>