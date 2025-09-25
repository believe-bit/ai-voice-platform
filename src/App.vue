<!-- src/App.vue -->
<template>
  <div id="app">
    <el-container class="main-container">
      <el-header class="header">
        <h1>AI智能语音实训平台</h1>
      </el-header>
      <el-container>
        <el-aside width="200px" class="sidebar">
          <el-menu :default-active="activePath" router>
            <el-menu-item index="/">
              <el-icon><House /></el-icon>
              <span>首页</span>
            </el-menu-item>
            <el-menu-item index="/speech-recognition">
              <el-icon><Microphone /></el-icon>
              <span>语音识别</span>
            </el-menu-item>
            <el-menu-item index="/offline-audio-recognition">
              <el-icon><Document /></el-icon>
              <span>离线音频文件识别</span>
            </el-menu-item>
            <el-menu-item index="/asr-finetune">
              <el-icon><Setting /></el-icon>
              <span>ASR模型微调</span>
            </el-menu-item>
            <el-menu-item index="/speech-synthesis">
              <el-icon><Phone /></el-icon>
              <span>语音合成</span>
            </el-menu-item>
            <el-menu-item index="/voice-clone">
              <el-icon><CopyDocument /></el-icon>
              <span>语音克隆</span>
            </el-menu-item>
            <el-menu-item index="/vits-train">
              <el-icon><Platform /></el-icon>
              <span>VITS模型训练</span>
            </el-menu-item>
            <el-menu-item index="/model-management">
              <el-icon><Folder /></el-icon>
              <span>模型管理</span>
            </el-menu-item>
            <el-menu-item index="/experiment-projects">
              <el-icon><Notebook /></el-icon>
              <span>实验项目</span>
            </el-menu-item>
            <el-menu-item index="/system-management">
              <el-icon><Tools /></el-icon>
              <span>系统管理</span>
            </el-menu-item>
          </el-menu>
        </el-aside>
        <el-main class="main-content">
          <router-view></router-view>
        </el-main>
      </el-container>
    </el-container>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue';
import { useRoute } from 'vue-router';
import { House, Microphone, Document, Setting, Phone, CopyDocument, Platform, Folder, Notebook, Tools } from '@element-plus/icons-vue';

const route = useRoute();
const activePath = ref(route.path);

watch(route, (to) => {
  activePath.value = to.path;
});
</script>

<style>
body {
  margin: 0;
  padding: 0;
  font-family: Arial, sans-serif;
}
.main-container {
  height: 100vh;
}
.header {
  background-color: #409EFF;
  color: white;
  text-align: center;
  line-height: 60px;
  display: flex; /* 使用 flex 布局 */
  justify-content: center; /* 水平居中 */
  align-items: center; /* 垂直居中 */
  padding-top: 5px; /* 添加顶部内边距，稍微上移文字 */
}
.header h1 {
  margin: 0; /* 移除 h1 默认外边距 */
  font-size: 24px; /* 可选：调整字体大小 */
}
.sidebar {
  background-color: #f0f0f0;
  height: 100%;
}
.main-content {
  padding: 20px;
}
</style>