<!-- src/components/ModelList.vue -->
<template>
  <div class="model-list-container">
    <el-row :gutter="20">
      <el-col :span="24">
        <el-input v-model="newModelName" placeholder="新模型名称" style="width: 200px; margin-right: 10px;" />
        <el-upload
          action="#"
          :http-request="handleUpload"
          :show-file-list="false"
          accept=".zip"
        >
          <el-button type="primary">上传 ZIP</el-button>
        </el-upload>
      </el-col>
    </el-row>
    <div style="margin-top: 20px;">
      <div v-show="!loading && isMounted">
        <el-table
          v-if="models.length > 0"
          :data="models"
          style="width: 100%;"
          :key="tableKey"
        >
          <el-table-column prop="name" label="模型名称" />
          <el-table-column label="操作">
            <template #default="scope">
              <el-button type="danger" size="small" @click="deleteModel(scope.row.name)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
        <p v-else>暂无 {{ sectionLabel }} 模型</p>
      </div>
      <div v-show="loading || !isMounted">
        <el-skeleton :rows="5" animated />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, nextTick } from 'vue';
import { debounce } from 'lodash';
import { ElMessage, ElSkeleton } from 'element-plus';
import { listModelFiles, uploadModelFile, deleteModelFile } from '../api';

const props = defineProps({
  section: String
});

const models = ref([]);
const newModelName = ref('');
const loading = ref(false);
const isMounted = ref(false);
const tableKey = ref(0); // 新增key强制重新渲染

const sectionLabel = computed(() => {
  const labels = {
    'asr': 'ASR',
    'asr-train': 'ASR训练',
    'tts': 'TTS',
    'voice': 'Voice',
    'vits-save': 'VITS保存'
  };
  return labels[props.section] || props.section;
});

const fetchModelList = async () => {
  loading.value = true;
  try {
    const response = await listModelFiles(props.section);
    console.log(`模型列表响应 (${props.section}):`, response.data);
    models.value = response.data.map(name => ({ name }));
    if (models.value.length === 0) {
      ElMessage.info(`暂无 ${sectionLabel.value} 模型`);
    }
  } catch (error) {
    console.error(`获取 ${props.section} 模型列表失败:`, error);
    models.value = [];
    ElMessage.warning(`无法加载 ${sectionLabel.value} 模型，请检查后端服务或目录权限`);
  } finally {
    loading.value = false;
    // 强制更新tableKey，确保el-table重新渲染
    tableKey.value += 1;
  }
};

const handleUpload = async (file) => {
  if (!newModelName.value) {
    ElMessage.error('请输入模型名称');
    return;
  }
  const formData = new FormData();
  formData.append('file', file.file);
  try {
    await uploadModelFile(props.section, newModelName.value, formData);
    ElMessage.success('模型上传成功');
    newModelName.value = '';
    fetchModelList();
  } catch (error) {
    ElMessage.error(error.response?.data?.error || '模型上传失败');
  }
};

const deleteModel = async (modelName) => {
  try {
    await deleteModelFile(props.section, modelName);
    ElMessage.success('模型删除成功');
    fetchModelList();
  } catch (error) {
    ElMessage.error(error.response?.data?.error || '模型删除失败');
  }
};

const debouncedFetchModelList = debounce(fetchModelList, 500);

onMounted(() => {
  debouncedFetchModelList();
  // 延长延迟时间，确保父容器尺寸稳定
  nextTick(() => {
    setTimeout(() => {
      isMounted.value = true;
    }, 300); // 从100ms增加到300ms
  });
});
</script>

<style scoped>
.model-list-container {
  width: 100%;
  box-sizing: border-box;
  padding: 10px;
}
.el-row {
  margin-bottom: 20px;
}
.el-table {
  width: 100%;
  max-height: 500px;
  overflow: auto;
  box-sizing: border-box;
}
</style>