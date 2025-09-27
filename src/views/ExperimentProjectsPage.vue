update<!-- views/ExperimentProjects.vue -->
<template>
  <div class="experiment-projects">
    <el-container>
      <el-aside width="250px" class="experiment-sidebar">
        <el-menu
          :default-active="activeExperiment"
          class="experiment-menu"
          @select="handleExperimentSelect"
        >
          <el-menu-item
            v-for="experiment in experiments"
            :key="experiment.id"
            :index="experiment.id"
          >
            <span>{{ experiment.name }}</span>
          </el-menu-item>
        </el-menu>
      </el-aside>
      <el-main class="experiment-content">
        <h2>{{ currentExperimentName }}</h2>
        <div v-if="currentExperimentComponent">
          <component :is="currentExperimentComponent" />
        </div>
        <div v-else>
          <p>未找到实验组件</p>
        </div>
      </el-main>
    </el-container>
  </div>
</template>

<script>
import { ref, computed } from 'vue';

// 每个实验的占位组件
const SpeechCollection = {
  template: `
    <div style="padding: 20px; background: #f8f9fa; border-radius: 8px; box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);">
      <h3 style="color: #333; margin-bottom: 20px;"></h3>
      <div style="display: flex; gap: 10px; margin-bottom: 15px;">
        <button 
          @click="startRecording" 
          style="padding: 8px 16px; background: #4CAF50; color: white; border: none; border-radius: 4px; cursor: pointer;"
        >
          开始录音
        </button>
        <button 
          @click="stopRecording" 
          style="padding: 8px 16px; background: #f44336; color: white; border: none; border-radius: 4px; cursor: pointer;"
        >
          停止录音
        </button>
      </div>
      <div v-if="isRecording" style="color: #4CAF50; font-weight: bold; margin-bottom: 15px;">
        录音中...
      </div>
      <div v-if="audioUrl" style="margin-top: 15px;">
        <audio controls :src="audioUrl" style="width: 100%; max-width: 400px;"></audio>
      </div>
    </div>
  `,
  setup() {
    const isRecording = ref(false);
    const audioUrl = ref(null);
    let mediaRecorder;
    let audioChunks = [];

    const startRecording = async () => {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        mediaRecorder = new MediaRecorder(stream);
        mediaRecorder.ondataavailable = (event) => {
          audioChunks.push(event.data);
        };
        mediaRecorder.onstop = () => {
          const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
          audioUrl.value = URL.createObjectURL(audioBlob);
          audioChunks = [];
        };
        mediaRecorder.start();
        isRecording.value = true;
      } catch (error) {
        console.error('录音失败:', error);
        alert('请确保已授予麦克风权限！');
      }
    };

    const stopRecording = () => {
      if (mediaRecorder && isRecording.value) {
        mediaRecorder.stop();
        isRecording.value = false;
      }
    };

    return {
      startRecording,
      stopRecording,
      isRecording,
      audioUrl,
    };
  },
};
const WaveformDisplay = {
  template: `
    <div style="padding: 20px; background: #f8f9fa; border-radius: 8px; box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);">
      <h3 style="color: #333; margin-bottom: 20px;">上传音频文件</h3>
      <div style="margin-bottom: 15px;">
        <input 
          type="file" 
          accept="audio/*" 
          @change="handleFileUpload" 
          style="display: none;" 
          id="audio-upload"
        />
        <label 
          for="audio-upload" 
          style="padding: 8px 16px; background: #2196F3; color: white; border-radius: 4px; cursor: pointer; display: inline-block;"
        >
          选择音频文件
        </label>
      </div>
      <div style="margin-top: 15px;">
        <audio v-if="audioUrl" controls :src="audioUrl" style="width: 100%; max-width: 400px; margin-bottom: 15px;"></audio>
        <canvas 
          ref="waveformCanvas" 
          width="600" 
          height="200" 
          style="background: #fff; border: 1px solid #ddd; border-radius: 4px; box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);"
        ></canvas>
      </div>
    </div>
  `,
  setup() {
    const audioUrl = ref(null);
    const waveformCanvas = ref(null);
    let audioContext = null;
    let reader = null;

    const handleFileUpload = (event) => {
      const file = event.target.files[0];
      if (!file) return;

      audioUrl.value = URL.createObjectURL(file);
      drawWaveform(file);
    };

    const drawWaveform = (file) => {
      audioContext = new (window.AudioContext || window.webkitAudioContext)();
      reader = new FileReader();

      reader.onload = (e) => {
        const arrayBuffer = e.target.result;
        audioContext.decodeAudioData(arrayBuffer).then((audioBuffer) => {
          const canvas = waveformCanvas.value;
          const ctx = canvas.getContext('2d');
          const data = audioBuffer.getChannelData(0);
          const step = Math.ceil(data.length / canvas.width);
          const amp = canvas.height / 2;

          ctx.clearRect(0, 0, canvas.width, canvas.height);
          ctx.beginPath();

          for (let i = 0; i < canvas.width; i++) {
            let min = 1.0;
            let max = -1.0;
            for (let j = 0; j < step; j++) {
              const datum = data[(i * step) + j];
              if (datum < min) min = datum;
              if (datum > max) max = datum;
            }
            ctx.moveTo(i, amp * (1 + min));
            ctx.lineTo(i, amp * (1 + max));
          }

          ctx.strokeStyle = '#4CAF50';
          ctx.stroke();
        });
      };

      reader.readAsArrayBuffer(file);
    };

    return {
      audioUrl,
      waveformCanvas,
      handleFileUpload,
    };
  },
};
const SpeechEncoding = {
  template: `
    <div style="padding: 20px; background: #f8f9fa; border-radius: 8px; box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);">
      <h3 style="color: #333; margin-bottom: 20px;">语音编码实验</h3>
      <div style="margin-bottom: 15px;">
        <input 
          type="file" 
          accept="audio/*" 
          @change="handleFileUpload" 
          style="display: none;" 
          id="audio-upload"
        />
        <label 
          for="audio-upload" 
          style="padding: 8px 16px; background: #2196F3; color: white; border-radius: 4px; cursor: pointer; display: inline-block;"
        >
          选择音频文件
        </label>
      </div>
      <div v-if="audioUrl" style="margin-top: 15px;">
        <audio controls :src="audioUrl" style="width: 100%; max-width: 400px; margin-bottom: 15px;"></audio>
        <div v-if="encodedData" style="margin-top: 15px;">
          <h4 style="color: #333; margin-bottom: 10px;">编码结果：</h4>
          <textarea 
            readonly 
            style="width: 100%; height: 100px; padding: 10px; border: 1px solid #ddd; border-radius: 4px;"
            :value="encodedData"
          ></textarea>
        </div>
      </div>
    </div>
  `,
  setup() {
    const audioUrl = ref(null);
    const encodedData = ref(null);

    const handleFileUpload = (event) => {
      const file = event.target.files[0];
      if (!file) return;

      audioUrl.value = URL.createObjectURL(file);
      encodeAudio(file);
    };

    const encodeAudio = (file) => {
      const reader = new FileReader();
      reader.onload = (e) => {
        const arrayBuffer = e.target.result;
        // 将 ArrayBuffer 转换为 Base64 编码
        const base64String = btoa(
          new Uint8Array(arrayBuffer).reduce(
            (data, byte) => data + String.fromCharCode(byte),
            ''
          )
        );
        encodedData.value = base64String;
      };
      reader.readAsArrayBuffer(file);
    };

    return {
      audioUrl,
      encodedData,
      handleFileUpload,
    };
  },
};

const SampleRateConversion = {
  template: `
    <div style="padding: 20px; background: #f8f9fa; border-radius: 8px; box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);">
      <h3 style="color: #333; margin-bottom: 20px;">语音采样频率转换实验</h3>
      <div style="margin-bottom: 15px;">
        <input 
          type="file" 
          accept="audio/*" 
          @change="handleFileUpload" 
          style="display: none;" 
          id="audio-upload"
        />
        <label 
          for="audio-upload" 
          style="padding: 8px 16px; background: #2196F3; color: white; border-radius: 4px; cursor: pointer; display: inline-block;"
        >
          选择音频文件
        </label>
      </div>
      <div v-if="audioUrl" style="margin-top: 15px;">
        <audio controls :src="audioUrl" style="width: 100%; max-width: 400px; margin-bottom: 15px;"></audio>
        <div style="margin-top: 15px;">
          <label style="margin-right: 10px;">目标采样频率：</label>
          <select v-model="targetSampleRate" style="padding: 5px; border-radius: 4px; border: 1px solid #ddd;">
            <option value="8000">8kHz</option>
            <option value="16000">16kHz</option>
            <option value="44100">44.1kHz</option>
            <option value="48000">48kHz</option>
          </select>
          <button 
            @click="convertSampleRate" 
            style="padding: 8px 16px; background: #4CAF50; color: white; border: none; border-radius: 4px; cursor: pointer; margin-left: 10px;"
          >
            转换
          </button>
        </div>
        <div v-if="convertedAudioUrl" style="margin-top: 15px;">
          <h4 style="color: #333; margin-bottom: 10px;">转换结果：</h4>
          <audio controls :src="convertedAudioUrl" style="width: 100%; max-width: 400px;"></audio>
          <a 
            :href="convertedAudioUrl" 
            download="converted_audio.wav" 
            style="padding: 8px 16px; background: #2196F3; color: white; border-radius: 4px; cursor: pointer; display: inline-block; margin-top: 10px;"
          >
            下载转换后的音频
          </a>
        </div>
      </div>
    </div>
  `,
  setup() {
    const audioUrl = ref(null);
    const convertedAudioUrl = ref(null);
    const targetSampleRate = ref("16000");
    let audioContext = null;

    const handleFileUpload = (event) => {
      const file = event.target.files[0];
      if (!file) return;

      audioUrl.value = URL.createObjectURL(file);
      convertedAudioUrl.value = null;
    };

    const convertSampleRate = async () => {
      if (!audioUrl.value) return;

      try {
        const response = await fetch(audioUrl.value);
        const arrayBuffer = await response.arrayBuffer();
        audioContext = new (window.AudioContext || window.webkitAudioContext)();
        const audioBuffer = await audioContext.decodeAudioData(arrayBuffer);

        // 创建离线音频上下文，用于采样率转换
        const offlineContext = new OfflineAudioContext(
          audioBuffer.numberOfChannels,
          audioBuffer.duration * targetSampleRate.value,
          parseInt(targetSampleRate.value)
        );

        const source = offlineContext.createBufferSource();
        source.buffer = audioBuffer;
        source.connect(offlineContext.destination);
        source.start();

        const convertedBuffer = await offlineContext.startRendering();
        const wavBlob = bufferToWav(convertedBuffer);
        convertedAudioUrl.value = URL.createObjectURL(wavBlob);
      } catch (error) {
        console.error('采样率转换失败:', error);
        alert('采样率转换失败，请重试！');
      }
    };

    const bufferToWav = (buffer) => {
      const numChannels = buffer.numberOfChannels;
      const length = buffer.length * numChannels * 2 + 44;
      const bufferArray = new ArrayBuffer(length);
      const view = new DataView(bufferArray);

      // WAV 文件头
      writeString(view, 0, 'RIFF');
      view.setUint32(4, 36 + buffer.length * numChannels * 2, true);
      writeString(view, 8, 'WAVE');
      writeString(view, 12, 'fmt ');
      view.setUint32(16, 16, true);
      view.setUint16(20, 1, true);
      view.setUint16(22, numChannels, true);
      view.setUint32(24, buffer.sampleRate, true);
      view.setUint32(28, buffer.sampleRate * numChannels * 2, true);
      view.setUint16(32, numChannels * 2, true);
      view.setUint16(34, 16, true);
      writeString(view, 36, 'data');
      view.setUint32(40, buffer.length * numChannels * 2, true);

      // 写入 PCM 数据
      let offset = 44;
      for (let i = 0; i < buffer.length; i++) {
        for (let channel = 0; channel < numChannels; channel++) {
          const sample = Math.max(-1, Math.min(1, buffer.getChannelData(channel)[i]));
          view.setInt16(offset, sample < 0 ? sample * 0x8000 : sample * 0x7FFF, true);
          offset += 2;
        }
      }

      return new Blob([view], { type: 'audio/wav' });
    };

    const writeString = (view, offset, string) => {
      for (let i = 0; i < string.length; i++) {
        view.setUint8(offset + i, string.charCodeAt(i));
      }
    };

    return {
      audioUrl,
      convertedAudioUrl,
      targetSampleRate,
      handleFileUpload,
      convertSampleRate,
    };
  },
};
const SamplingFrequency = {
  template: `
    <div style="padding: 20px; background: #f8f9fa; border-radius: 8px; box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);">
      <h3 style="color: #333; margin-bottom: 20px;">语音采样频率转换实验</h3>
      <div style="margin-bottom: 15px;">
        <input 
          type="file" 
          accept="audio/*" 
          @change="handleFileUpload" 
          style="display: none;" 
          id="audio-upload"
        />
        <label 
          for="audio-upload" 
          style="padding: 8px 16px; background: #2196F3; color: white; border-radius: 4px; cursor: pointer; display: inline-block;"
        >
          选择音频文件
        </label>
      </div>
      <div v-if="audioUrl" style="margin-top: 15px;">
        <audio controls :src="audioUrl" style="width: 100%; max-width: 400px; margin-bottom: 15px;"></audio>
        <div style="margin-top: 15px;">
          <label style="margin-right: 10px;">目标采样频率：</label>
          <select v-model="targetSampleRate" style="padding: 5px; border-radius: 4px; border: 1px solid #ddd;">
            <option value="8000">8kHz</option>
            <option value="16000">16kHz</option>
            <option value="44100">44.1kHz</option>
            <option value="48000">48kHz</option>
          </select>
          <button 
            @click="convertSampleRate" 
            style="padding: 8px 16px; background: #4CAF50; color: white; border: none; border-radius: 4px; cursor: pointer; margin-left: 10px;"
          >
            转换
          </button>
        </div>
        <div v-if="convertedAudioUrl" style="margin-top: 15px;">
          <h4 style="color: #333; margin-bottom: 10px;">转换结果：</h4>
          <audio controls :src="convertedAudioUrl" style="width: 100%; max-width: 400px;"></audio>
          <a 
            :href="convertedAudioUrl" 
            download="converted_audio.wav" 
            style="padding: 8px 16px; background: #2196F3; color: white; border-radius: 4px; cursor: pointer; display: inline-block; margin-top: 10px;"
          >
            下载转换后的音频
          </a>
        </div>
      </div>
    </div>
  `,
  setup() {
    const audioUrl = ref(null);
    const convertedAudioUrl = ref(null);
    const targetSampleRate = ref("16000");
    let audioContext = null;

    const handleFileUpload = (event) => {
      const file = event.target.files[0];
      if (!file) return;

      audioUrl.value = URL.createObjectURL(file);
      convertedAudioUrl.value = null;
    };

    const convertSampleRate = async () => {
      if (!audioUrl.value) return;

      try {
        const response = await fetch(audioUrl.value);
        const arrayBuffer = await response.arrayBuffer();
        audioContext = new (window.AudioContext || window.webkitAudioContext)();
        const audioBuffer = await audioContext.decodeAudioData(arrayBuffer);

        // 创建离线音频上下文，用于采样率转换
        const offlineContext = new OfflineAudioContext(
          audioBuffer.numberOfChannels,
          audioBuffer.duration * targetSampleRate.value,
          parseInt(targetSampleRate.value)
        );

        const source = offlineContext.createBufferSource();
        source.buffer = audioBuffer;
        source.connect(offlineContext.destination);
        source.start();

        const convertedBuffer = await offlineContext.startRendering();
        const wavBlob = bufferToWav(convertedBuffer);
        convertedAudioUrl.value = URL.createObjectURL(wavBlob);
      } catch (error) {
        console.error('采样率转换失败:', error);
        alert('采样率转换失败，请重试！');
      }
    };

    const bufferToWav = (buffer) => {
      const numChannels = buffer.numberOfChannels;
      const length = buffer.length * numChannels * 2 + 44;
      const bufferArray = new ArrayBuffer(length);
      const view = new DataView(bufferArray);

      // WAV 文件头
      writeString(view, 0, 'RIFF');
      view.setUint32(4, 36 + buffer.length * numChannels * 2, true);
      writeString(view, 8, 'WAVE');
      writeString(view, 12, 'fmt ');
      view.setUint32(16, 16, true);
      view.setUint16(20, 1, true);
      view.setUint16(22, numChannels, true);
      view.setUint32(24, buffer.sampleRate, true);
      view.setUint32(28, buffer.sampleRate * numChannels * 2, true);
      view.setUint16(32, numChannels * 2, true);
      view.setUint16(34, 16, true);
      writeString(view, 36, 'data');
      view.setUint32(40, buffer.length * numChannels * 2, true);

      // 写入 PCM 数据
      let offset = 44;
      for (let i = 0; i < buffer.length; i++) {
        for (let channel = 0; channel < numChannels; channel++) {
          const sample = Math.max(-1, Math.min(1, buffer.getChannelData(channel)[i]));
          view.setInt16(offset, sample < 0 ? sample * 0x8000 : sample * 0x7FFF, true);
          offset += 2;
        }
      }

      return new Blob([view], { type: 'audio/wav' });
    };

    const writeString = (view, offset, string) => {
      for (let i = 0; i < string.length; i++) {
        view.setUint8(offset + i, string.charCodeAt(i));
      }
    };

    return {
      audioUrl,
      convertedAudioUrl,
      targetSampleRate,
      handleFileUpload,
      convertSampleRate,
    };
  },
};
const SignalStrength = {
  template: `
    <div style="padding: 20px; background: #f8f9fa; border-radius: 8px; box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);">
      <h3 style="color: #333; margin-bottom: 20px;">语音信号强度实验</h3>
      <div style="margin-bottom: 15px;">
        <input 
          type="file" 
          accept="audio/*" 
          @change="handleFileUpload" 
          style="display: none;" 
          id="audio-upload"
        />
        <label 
          for="audio-upload" 
          style="padding: 8px 16px; background: #2196F3; color: white; border-radius: 4px; cursor: pointer; display: inline-block;"
        >
          选择音频文件
        </label>
      </div>
      <div v-if="audioUrl" style="margin-top: 15px;">
        <audio controls :src="audioUrl" style="width: 100%; max-width: 400px; margin-bottom: 15px;"></audio>
        <button 
          @click="analyzeSignalStrength" 
          :disabled="isAnalyzing"
          style="padding: 8px 16px; background: #4CAF50; color: white; border: none; border-radius: 4px; cursor: pointer;"
        >
          {{ isAnalyzing ? '分析中...' : '分析信号强度' }}
        </button>
        <div v-if="rmsValue !== null" style="margin-top: 15px;">
          <h4 style="color: #333; margin-bottom: 10px;">信号强度分析结果：</h4>
          <p>RMS 值：{{ rmsValue.toFixed(4) }}</p>
          <p>峰值强度：{{ peakValue.toFixed(4) }}</p>
          <canvas 
            ref="strengthCanvas" 
            width="600" 
            height="200" 
            style="background: #fff; border: 1px solid #ddd; border-radius: 4px; box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1); margin-top: 10px;"
          ></canvas>
        </div>
      </div>
    </div>
  `,
  setup() {
    const audioUrl = ref(null);
    const rmsValue = ref(null);
    const peakValue = ref(null);
    const strengthCanvas = ref(null);
    const isAnalyzing = ref(false);
    const audioContext = new (window.AudioContext || window.webkitAudioContext)();

    const handleFileUpload = (event) => {
      const file = event.target.files[0];
      if (!file) return;

      audioUrl.value = URL.createObjectURL(file);
      rmsValue.value = null;
      peakValue.value = null;
    };

    const analyzeSignalStrength = async () => {
      if (!audioUrl.value || isAnalyzing.value) return;

      isAnalyzing.value = true;

      try {
        // 加载音频数据
        const response = await fetch(audioUrl.value);
        const arrayBuffer = await response.arrayBuffer();
        const audioBuffer = await audioContext.decodeAudioData(arrayBuffer);

        // 计算 RMS 值和峰值强度
        const channelData = audioBuffer.getChannelData(0);
        let sumOfSquares = 0;
        let peak = 0;

        for (let i = 0; i < channelData.length; i++) {
          const sample = channelData[i];
          sumOfSquares += sample * sample;
          peak = Math.max(peak, Math.abs(sample));
        }

        const rms = Math.sqrt(sumOfSquares / channelData.length);
        rmsValue.value = rms;
        peakValue.value = peak;

        // 绘制信号强度图表
        drawStrengthChart(channelData);
      } catch (error) {
        console.error('信号强度分析失败:', error);
        alert('信号强度分析失败，请重试！');
      } finally {
        isAnalyzing.value = false;
      }
    };

    const drawStrengthChart = (channelData) => {
      const canvas = strengthCanvas.value;
      const ctx = canvas.getContext('2d');
      const width = canvas.width;
      const height = canvas.height;
      const step = Math.ceil(channelData.length / width);

      ctx.clearRect(0, 0, width, height);
      ctx.beginPath();
      ctx.moveTo(0, height / 2);

      for (let i = 0; i < width; i++) {
        const start = i * step;
        const end = Math.min(start + step, channelData.length);
        let sum = 0;

        for (let j = start; j < end; j++) {
          sum += Math.abs(channelData[j]);
        }

        const avg = sum / (end - start);
        const y = (1 - avg) * (height / 2);
        ctx.lineTo(i, y);
      }

      ctx.strokeStyle = '#4CAF50';
      ctx.stroke();
    };

    return {
      audioUrl,
      rmsValue,
      peakValue,
      strengthCanvas,
      handleFileUpload,
      analyzeSignalStrength,
    };
  },
};
const WhiteNoise = {
  template: `
    <div style="padding: 20px; background: #f8f9fa; border-radius: 8px; box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);">
      <h3 style="color: #333; margin-bottom: 20px;">白噪音信号实验</h3>
      <div style="margin-bottom: 15px;">
        <label style="margin-right: 10px;">持续时间（秒）：</label>
        <input 
          type="number" 
          v-model="duration" 
          min="1" 
          max="10" 
          style="padding: 5px; border-radius: 4px; border: 1px solid #ddd; width: 60px;"
        />
      </div>
      <div style="display: flex; gap: 10px; margin-bottom: 15px;">
        <button 
          @click="generateWhiteNoise" 
          :disabled="isPlaying" 
          style="padding: 8px 16px; background: #4CAF50; color: white; border: none; border-radius: 4px; cursor: pointer;"
        >
          生成白噪音
        </button>
        <button 
          @click="stopWhiteNoise" 
          :disabled="!isPlaying" 
          style="padding: 8px 16px; background: #f44336; color: white; border: none; border-radius: 4px; cursor: pointer;"
        >
          停止播放
        </button>
      </div>
      <div v-if="audioUrl" style="margin-top: 15px;">
        <audio controls :src="audioUrl" style="width: 100%; max-width: 400px; margin-bottom: 15px;"></audio>
        <a 
          :href="audioUrl" 
          download="white_noise.wav" 
          style="padding: 8px 16px; background: #2196F3; color: white; border-radius: 4px; cursor: pointer; display: inline-block;"
        >
          下载白噪音
        </a>
      </div>
    </div>
  `,
  setup() {
    const duration = ref(3);
    const isPlaying = ref(false);
    const audioUrl = ref(null);
    let audioContext = null;
    let noiseNode = null;
    let mediaStreamDestination = null;

    const generateWhiteNoise = () => {
      if (isPlaying.value) return;

      try {
        audioContext = new (window.AudioContext || window.webkitAudioContext)();
        mediaStreamDestination = audioContext.createMediaStreamDestination();

        // 创建白噪音节点
        noiseNode = audioContext.createScriptProcessor(4096, 1, 1);
        noiseNode.onaudioprocess = (e) => {
          const output = e.outputBuffer.getChannelData(0);
          for (let i = 0; i < output.length; i++) {
            output[i] = Math.random() * 2 - 1; // 生成 -1 到 1 之间的随机数
          }
        };

        // 连接节点并播放
        noiseNode.connect(mediaStreamDestination);
        noiseNode.connect(audioContext.destination);
        isPlaying.value = true;

        // 录制白噪音
        const mediaRecorder = new MediaRecorder(mediaStreamDestination.stream);
        const audioChunks = [];

        mediaRecorder.ondataavailable = (e) => {
          audioChunks.push(e.data);
        };

        mediaRecorder.onstop = () => {
          const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
          audioUrl.value = URL.createObjectURL(audioBlob);
        };

        mediaRecorder.start();
        setTimeout(() => {
          mediaRecorder.stop();
          stopWhiteNoise();
        }, duration.value * 1000);
      } catch (error) {
        console.error('生成白噪音失败:', error);
        alert('生成白噪音失败，请重试！');
      }
    };

    const stopWhiteNoise = () => {
      if (noiseNode) {
        noiseNode.disconnect();
        noiseNode = null;
      }
      if (audioContext) {
        audioContext.close();
        audioContext = null;
      }
      isPlaying.value = false;
    };

    return {
      duration,
      isPlaying,
      audioUrl,
      generateWhiteNoise,
      stopWhiteNoise,
    };
  },
};
const ShortTimeFourier = {
  template: `
    <div style="padding: 20px; background: #f8f9fa; border-radius: 8px; box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);">
      <h3 style="color: #333; margin-bottom: 20px;">语音短时傅里叶变换实验</h3>
      <div style="margin-bottom: 15px;">
        <input 
          type="file" 
          accept="audio/*" 
          @change="handleFileUpload" 
          style="display: none;" 
          id="stft-upload"
        />
        <label 
          for="stft-upload" 
          style="padding: 8px 16px; background: #2196F3; color: white; border-radius: 4px; cursor: pointer; display: inline-block;"
        >
          选择音频文件
        </label>
      </div>
      <div v-if="audioUrl" style="margin-top: 15px;">
        <audio controls :src="audioUrl" style="width: 100%; max-width: 400px; margin-bottom: 15px;"></audio>
        <div style="display: flex; gap: 10px; margin-bottom: 15px;">
          <button 
            @click="analyzeSTFT" 
            :disabled="isAnalyzing" 
            style="padding: 8px 16px; background: #4CAF50; color: white; border: none; border-radius: 4px; cursor: pointer;"
          >
            {{ isAnalyzing ? '分析中...' : '分析频谱' }}
          </button>
          <div v-if="isAnalyzing" style="display: flex; align-items: center; color: #666;">
            <span>正在处理音频，请稍候...</span>
          </div>
        </div>
        <div v-if="spectrogramData" style="margin-top: 15px;">
          <h4 style="color: #333; margin-bottom: 10px;">频谱图：</h4>
          <canvas 
            ref="spectrogramCanvas" 
            width="600" 
            height="300" 
            style="background: #fff; border: 1px solid #ddd; border-radius: 4px; box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);"
          ></canvas>
        </div>
      </div>
    </div>
  `,
  setup() {
    const audioUrl = ref(null);
    const spectrogramData = ref(null);
    const spectrogramCanvas = ref(null);
    const isAnalyzing = ref(false);
    let audioContext = null;

    const handleFileUpload = (event) => {
      const file = event.target.files[0];
      if (!file) return;

      audioUrl.value = URL.createObjectURL(file);
      spectrogramData.value = null;
    };

    const analyzeSTFT = async () => {
      if (!audioUrl.value || isAnalyzing.value) return;

      isAnalyzing.value = true;

      try {
        // 加载音频数据
        const response = await fetch(audioUrl.value);
        if (!response.ok) {
          throw new Error(`音频文件加载失败: ${response.status} ${response.statusText}`);
        }
        const arrayBuffer = await response.arrayBuffer();
        audioContext = new (window.AudioContext || window.webkitAudioContext)();
        const audioBuffer = await audioContext.decodeAudioData(arrayBuffer).catch(error => {
          throw new Error(`音频解码失败: ${error.message}`);
        });

        // 获取音频数据
        const channelData = audioBuffer.getChannelData(0);
        const sampleRate = audioBuffer.sampleRate;
        const windowSize = 1024; // 窗口大小
        const hopSize = 512; // 跳跃大小

        // 检查音频数据长度是否足够
        if (channelData.length < windowSize) {
          throw new Error(`音频数据长度不足，至少需要 ${windowSize} 个采样点`);
        }

        // 计算 STFT
        const stftResult = computeSTFT(channelData, windowSize, hopSize);
        spectrogramData.value = stftResult;

        // 绘制频谱图
        drawSpectrogram(stftResult, sampleRate, hopSize);
      } catch (error) {
        console.error('STFT 分析失败:', error);
        alert(`STFT 分析失败: ${error.message}`);
      } finally {
        isAnalyzing.value = false;
      }
    };

    const computeSTFT = (data, windowSize, hopSize) => {
      const stft = [];
      const hannWindow = new Array(windowSize).fill(0).map((_, i) => {
        return 0.5 * (1 - Math.cos((2 * Math.PI * i) / (windowSize - 1)));
      });

      for (let i = 0; i < data.length - windowSize; i += hopSize) {
        const segment = data.slice(i, i + windowSize);
        const windowedSegment = segment.map((sample, idx) => sample * hannWindow[idx]);
        const fft = computeFFT(windowedSegment);
        stft.push(fft);
      }

      return stft;
    };

    const computeFFT = (data) => {
      const n = data.length;
      const fft = new Array(n / 2).fill(0);

      for (let k = 0; k < n / 2; k++) {
        let real = 0;
        let imag = 0;

        for (let t = 0; t < n; t++) {
          const angle = (2 * Math.PI * k * t) / n;
          real += data[t] * Math.cos(angle);
          imag -= data[t] * Math.sin(angle);
        }

        fft[k] = Math.sqrt(real * real + imag * imag);
      }

      return fft;
    };

    const drawSpectrogram = (stftResult, sampleRate, hopSize) => {
      try {
        if (!spectrogramCanvas.value) {
          throw new Error('Canvas 元素未正确初始化');
        }
        const canvas = spectrogramCanvas.value;
        const ctx = canvas.getContext('2d');
        if (!ctx) {
          throw new Error('无法获取 Canvas 的 2D 上下文');
        }
        const width = canvas.width;
        const height = canvas.height;

        ctx.clearRect(0, 0, width, height);

        // 限制频谱图的分辨率以避免性能问题
        const maxPoints = 1000;
        const step = Math.max(1, Math.floor(stftResult.length / maxPoints));
        const maxMagnitude = Math.max(...stftResult.flat());

        for (let i = 0; i < stftResult.length; i += step) {
          for (let j = 0; j < stftResult[i].length; j++) {
            const x = (i / stftResult.length) * width;
            const y = height - (j / stftResult[i].length) * height;
            const magnitude = stftResult[i][j] / maxMagnitude;
            const intensity = Math.min(255, Math.floor(magnitude * 255));
            ctx.fillStyle = `rgb(${intensity}, ${intensity}, ${intensity})`;
            ctx.fillRect(x, y, 1, 1);
          }
        }
      } catch (error) {
        console.error('绘制频谱图失败:', error);
        throw new Error(`绘制频谱图失败: ${error.message}`);
      }
    };

    return {
      audioUrl,
      spectrogramData,
      spectrogramCanvas,
      isAnalyzing,
      handleFileUpload,
      analyzeSTFT,
    };
  },
};
const AutoGainControl = {
  template: '<div>音频自动增益频控制实验 - 功能待实现</div>',
};
const EndpointDetection = {
  template: '<div>语音端点检测实验 - 功能待实现</div>',
};
const NoiseClassification = {
  template: '<div>语音噪音类实验 - 功能待实现</div>',
};
const SpeechEnhancement = {
  template: '<div>语音增强实验 - 功能待实现</div>',
};
const AddNoise = {
  template: '<div>语音添加噪音实验 - 功能待实现</div>',
};
const EmotionAnalysis = {
  template: '<div>情感分析实验 - 功能待实现</div>',
};
const RealTimeLocalization = {
  template: '<div>实时声源定位实验 - 功能待实现</div>',
};
const WordSegmentation = {
  template: '<div>分词识别实验 - 功能待实现</div>',
};
const PosTagging = {
  template: '<div>词性标注实验 - 功能待实现</div>',
};
const NamedEntityRecognition = {
  template: '<div>命名识别实验 - 功能待实现</div>',
};

export default {
  name: 'ExperimentProjectsPage',
  components: {
    SpeechCollection,
    WaveformDisplay,
    SpeechEncoding,
    SamplingFrequency,
    SignalStrength,
    WhiteNoise,
    ShortTimeFourier,
    AutoGainControl,
    EndpointDetection,
    NoiseClassification,
    SpeechEnhancement,
    AddNoise,
    EmotionAnalysis,
    RealTimeLocalization,
    WordSegmentation,
    PosTagging,
    NamedEntityRecognition,
  },
  setup() {
    // 实验列表
    const experiments = [
      { id: 'speech-collection', name: '语音采集实验', component: SpeechCollection },
      { id: 'waveform-display', name: '语音波形显示实验', component: WaveformDisplay },
      { id: 'speech-encoding', name: '语音编码实验', component: SpeechEncoding },
      { id: 'sampling-frequency', name: '语音采样频率转换实验', component: SamplingFrequency },
      { id: 'signal-strength', name: '语音信号强度实验', component: SignalStrength },
      { id: 'white-noise', name: '白噪音信号实验', component: WhiteNoise },
      { id: 'short-time-fourier', name: '语音短时傅里叶变换实验', component: ShortTimeFourier },
      { id: 'auto-gain-control', name: '音频自动增益频控制实验', component: AutoGainControl },
      { id: 'endpoint-detection', name: '语音端点检测实验', component: EndpointDetection },
      { id: 'noise-classification', name: '语音噪音类实验', component: NoiseClassification },
      { id: 'speech-enhancement', name: '语音增强实验', component: SpeechEnhancement },
      { id: 'add-noise', name: '语音添加噪音实验', component: AddNoise },
      { id: 'emotion-analysis', name: '情感分析实验', component: EmotionAnalysis },
      { id: 'real-time-localization', name: '实时声源定位实验', component: RealTimeLocalization },
      { id: 'word-segmentation', name: '分词识别实验', component: WordSegmentation },
      { id: 'pos-tagging', name: '词性标注实验', component: PosTagging },
      { id: 'named-entity-recognition', name: '命名识别实验', component: NamedEntityRecognition },
    ];

    // 当前选中的实验
    const activeExperiment = ref('speech-collection');
    console.log('初始 activeExperiment:', activeExperiment.value); // 调试日志

    // 处理实验选择
    const handleExperimentSelect = (index) => {
      activeExperiment.value = index;
    };

    // 计算当前实验的组件
    const currentExperimentComponent = computed(() => {
      const experiment = experiments.find((exp) => exp.id === activeExperiment.value);
      return experiment ? experiment.component : SpeechCollection;
    });

    // 计算当前实验的名称
    const currentExperimentName = computed(() => {
      const experiment = experiments.find((exp) => exp.id === activeExperiment.value);
      return experiment ? experiment.name : '实验项目';
    });

    return {
      experiments,
      activeExperiment,
      handleExperimentSelect,
      currentExperimentComponent,
      currentExperimentName,
    };
  },
};
</script>

<style scoped>
.experiment-projects {
  height: 100%;
}
.experiment-sidebar {
  background-color: #f5f5f5;
  border-right: 1px solid #e6e6e6;
}
.experiment-menu {
  background-color: transparent;
}
.experiment-content {
  padding: 20px;
  min-height: 300px;
  display: flex;
  flex-direction: column;
  align-items: center;
}
.experiment-content h2 {
  margin-top: 0;
}
</style>