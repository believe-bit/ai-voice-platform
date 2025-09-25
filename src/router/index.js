// src/router/index.js
import { createRouter, createWebHistory } from 'vue-router';

const HomePage = () => import('../views/HomePage.vue');
const SpeechRecognitionPage = () => import('../views/SpeechRecognitionPage.vue');
const OfflineAudioRecognitionPage = () => import('../views/OfflineAudioRecognitionPage.vue');
const ASRFinetunePage = () => import('../views/ASRFinetunePage.vue');
const SpeechSynthesisPage = () => import('../views/SpeechSynthesisPage.vue');
const VoiceClonePage = () => import('../views/VoiceClonePage.vue');
const VITSTrainPage = () => import('../views/VITSTrainPage.vue');
const ModelManagementPage = () => import('../views/ModelManagementPage.vue');
const ExperimentProjectsPage = () => import('../views/ExperimentProjectsPage.vue');
const SystemManagementPage = () => import('../views/SystemManagementPage.vue');

const routes = [
  { path: '/', component: HomePage },
  { path: '/speech-recognition', component: SpeechRecognitionPage },
  { path: '/offline-audio-recognition', component: OfflineAudioRecognitionPage },
  { path: '/asr-finetune', component: ASRFinetunePage },
  { path: '/speech-synthesis', component: SpeechSynthesisPage },
  { path: '/voice-clone', component: VoiceClonePage },
  { path: '/vits-train', component: VITSTrainPage },
  { path: '/model-management', component: ModelManagementPage },
  { path: '/experiment-projects', component: ExperimentProjectsPage },
  { path: '/system-management', component: SystemManagementPage }
];

const router = createRouter({
  history: createWebHistory(process.env.BASE_URL),
  routes
});

export default router;