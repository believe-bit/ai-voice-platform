// src/api/index.js
import axios from 'axios';

const API_BASE_URL = 'http://localhost:5000';

export const getModels = () => axios.get(`${API_BASE_URL}/models`);
export const loadModel = (model) => axios.post(`${API_BASE_URL}/load_model`, { model });
export const recognizeAudio = (formData) => axios.post(`${API_BASE_URL}/recognize`, formData, {
  headers: { 'Content-Type': 'multipart/form-data' }
});
export const listModels = (section) => axios.get(`${API_BASE_URL}/list_models?section=${section}`);
export const uploadDataset = (formData) => axios.post(`${API_BASE_URL}/upload_dataset`, formData, {
  headers: { 'Content-Type': 'multipart/form-data' }
});
export const startAsrTrain = (data) => axios.post(`${API_BASE_URL}/start_training`, data);
export const stopAsrTrain = () => axios.post(`${API_BASE_URL}/stop_training`);
export const getStreamLogs = () => `${API_BASE_URL}/stream_logs`;
export const listVoiceModels = () => axios.get(`${API_BASE_URL}/list_voice_models`);
export const uploadCloneAudio = (formData) => axios.post(`${API_BASE_URL}/upload_clone_audio`, formData, {
  headers: { 'Content-Type': 'multipart/form-data' }
});

export const startVitsTrain = (data) => axios.post(`${API_BASE_URL}/vits_train`, data);
export const stopVitsTrain = () => axios.post(`${API_BASE_URL}/vits_stop_train`);
export const vitsTest = (data) => axios.post(`${API_BASE_URL}/vits_test`, data);
export const getVitsTrainLog = () => `${API_BASE_URL}/vits_train_log`;
export const getVitsTestLog = () => `${API_BASE_URL}/vits_test_log`;

export const listModelFiles = (section) => axios.get(`${API_BASE_URL}/list_models?section=${section}`);
export const uploadModelFile = (section, modelName, formData) => axios.post(`${API_BASE_URL}/upload_model_file?section=${section}&model_name=${modelName}`, formData, {
  headers: { 'Content-Type': 'multipart/form-data' }
});
export const deleteModelFile = (section, modelName) => axios.post(`${API_BASE_URL}/delete_model_file?section=${section}&model_name=${modelName}`);