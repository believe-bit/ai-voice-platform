<!-- src/views/ModelManagementPage.vue -->
<template>
  <div class="model-management">
    <h2>模型管理</h2>
    <el-tabs v-model="activeTab" type="card" :animated="false">
      <el-tab-pane lazy label="ASR模型" name="asr" key="asr">
        <ModelList section="asr" />
      </el-tab-pane>
      <el-tab-pane lazy label="ASR训练模型" name="asr-train" key="asr-train">
        <ModelList section="asr-train" />
      </el-tab-pane>
      <el-tab-pane lazy label="TTS模型" name="tts" key="tts">
        <ModelList section="tts" />
      </el-tab-pane>
      <el-tab-pane lazy label="Voice模型" name="voice" key="voice">
        <ModelList section="voice" />
      </el-tab-pane>
      <el-tab-pane lazy label="VITS保存模型" name="vits-save" key="vits-save">
        <ModelList section="vits-save" />
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue';
import { debounce } from 'lodash';
import ModelList from './ModelList.vue';

const activeTab = ref('asr');

// 防抖处理标签页切换
const debouncedTabChange = debounce((newTab) => {
  console.log(`切换到标签页: ${newTab}`);
}, 300);

watch(activeTab, (newTab) => {
  debouncedTabChange(newTab);
});
</script>

<style scoped>
.model-management {
  width: 100%;
  box-sizing: border-box;
  padding: 20px;
}
:deep(.el-tabs__content) {
  min-height: 400px;
  width: 100%;
  box-sizing: border-box;
  transition: none !important; /* 禁用动画 */
}
:deep(.el-tab-pane) {
  width: 100%;
  box-sizing: border-box;
}
</style>