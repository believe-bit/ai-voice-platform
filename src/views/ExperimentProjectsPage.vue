<!-- views/ExperimentProjects.vue -->
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
    <div style="padding: 20px;">
      <h3></h3>
      <button @click="startRecording" style="margin-right: 10px;">开始录音</button>
      <button @click="stopRecording">停止录音</button>
      <div v-if="isRecording" style="margin-top: 10px; color: green;">录音中...</div>
      <div v-if="audioUrl" style="margin-top: 10px;">
        <audio controls :src="audioUrl"></audio>
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
    <div style="padding: 20px;">
      <h3>语音波形显示实验</h3>
      <input type="file" accept="audio/*" @change="handleFileUpload" />
      <div v-if="audioUrl" style="margin-top: 20px;">
        <audio controls :src="audioUrl"></audio>
        <canvas ref="waveformCanvas" width="600" height="200" style="margin-top: 20px; border: 1px solid #ccc;"></canvas>
      </div>
    </div>
  `,
  setup() {
    const audioUrl = ref(null);
    const waveformCanvas = ref(null);

    const handleFileUpload = (event) => {
      const file = event.target.files[0];
      if (!file) return;

      audioUrl.value = URL.createObjectURL(file);
      drawWaveform(file);
    };

    const drawWaveform = (file) => {
      const audioContext = new (window.AudioContext || window.webkitAudioContext)();
      const reader = new FileReader();

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
            const min = 1.0;
            const max = -1.0;
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
  template: '<div>语音编码实验 - 功能待实现</div>',
};
const SamplingFrequency = {
  template: '<div>语音采样频率转换实验 - 功能待实现</div>',
};
const SignalStrength = {
  template: '<div>语音信号强度实验 - 功能待实现</div>',
};
const WhiteNoise = {
  template: '<div>白噪音信号实验 - 功能待实现</div>',
};
const ShortTimeFourier = {
  template: '<div>语音短时傅里叶变换实验 - 功能待实现</div>',
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