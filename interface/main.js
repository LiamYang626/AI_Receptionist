// main.js
$(document).ready(function(){

  // Initialize textillate for the Siri message.
  $('.siri-message').textillate({
    loop: true,
    sync: true,
    in: { effect: "fadeInUp", sync: true },
    out: { effect: "fadeOutUp", sync: true }
  });

  // Initialize SiriWave.
  const siriWave = new SiriWave({
    container: document.getElementById("siri-container"),
    width: 800,
    height: 200,
    style: "ios9",
    amplitude: 1,
    speed: 0.30,
    autostart: true
  });

  function runAudioVisualizer() {
    navigator.mediaDevices.getUserMedia({ audio: true, video: false })
      .then(stream => {
        const AudioCtx = window.AudioContext || window.webkitAudioContext;
        const ctx = new AudioCtx();
        const source = ctx.createMediaStreamSource(stream);
        const analyser = ctx.createAnalyser();

        // FFT 크기 설정 (원본 예제의 대략 5Hz 갱신 기준)
        const approxVisFreq = 5;
        const sampleRate = ctx.sampleRate;
        const totalSamples = sampleRate / approxVisFreq;
        analyser.fftSize = 2 ** Math.floor(Math.log2(totalSamples));

        source.connect(analyser);
        siriWave.start();

        const freqData = new Uint8Array(analyser.frequencyBinCount);
        const timeData = new Uint8Array(analyser.frequencyBinCount);

        function updateVisual() {
          // 주파수 스펙트럼
          analyser.getByteFrequencyData(freqData);
          // 시간 도메인(파형) 데이터
          analyser.getByteTimeDomainData(timeData);

          // 1) 진폭 계산: 파형의 최대치에서 128 빼기
          const amp = timeData.reduce((max, v) => Math.max(max, v), 128) - 128;
          const normAmp = amp / 128 * 10;        // [0..10] 범위
          siriWave.setAmplitude(normAmp);

          // 2) 최고 주파수 빈(bin) 찾기
          let maxBin = 0;
          for (let i = 1; i < freqData.length; i++) {
            if (freqData[i] > freqData[maxBin]) maxBin = i;
          }
          const freq = maxBin * (sampleRate / 2) / analyser.frequencyBinCount;
          siriWave.setSpeed(freq / 10000);       // [0..~2] 범위 조정

          requestAnimationFrame(updateVisual);
        }

        updateVisual();
      })
      .catch(err => console.error("Audio visualizer error:", err));
  }
  runAudioVisualizer();

  let currentMessage = "";

  updateUI("Initializing...");

  async function pollMessages() {
    try {
      const response = await fetch("http://127.0.0.1:5500/message?t=" + Date.now(), { cache: "no-store" });
      if (!response.ok) {
        console.error("HTTP error:", response.status);
        setTimeout(pollMessages, 1000);
        return;
      }
      const audio_response = await fetch("http://127.0.0.1:5500/audio");
      if (!audio_response.ok) {
        console.error("HTTP error:", audio_response.status);
        setTimeout(pollMessages, 1000);
        return;
      }
      const data = await response.json();
      if (data.text !== currentMessage){
        console.log("Received message:", data.text);
        updateUI(data.text);
        currentMessage = data.text;
        if(data.text !== "Listening..." && data.text !== "Transcribing..." && data.text !== "Processing...") {
          let audioPlayer = document.getElementById("audioPlayer");
          if (audioPlayer) {
            audioPlayer.src = "http://127.0.0.1:5500/audio?t=" + Date.now();
            audioPlayer
            audioPlayer.play().catch(e => console.error("Audio play error:", e));
          }
        }

      }
      // 메시지를 수신하면 즉시 다음 메시지를 기다림 (롱 폴링)
      pollMessages();
      } catch (error) {
        console.error("Polling error:", error);
        setTimeout(pollMessages, 1000);
    }
  }

  function updateUI(messageText) {
    $('.siri-message').find('ul.texts li').text(messageText);
    $('.siri-message').textillate('start');
  }

  let audioPlayer = document.getElementById("audioPlayer");
  if (audioPlayer) {
    audioPlayer.addEventListener("ended", function() {
      console.log("Audio playback ended.");
      // Send a POST request to notify the server that audio playback finished.
      fetch("http://127.0.0.1:5500/audio_finished", {
          method: "POST",
          headers: {
              "Content-Type": "application/json"
          },
          body: JSON.stringify({ status: "audio_ended" })
      })
      .then(response => response.json())
      .then(data => console.log("Audio finished signal sent, server response:", data))
      .catch(error => console.error("Error sending audio finished signal:", error));
    });
  }

  // 페이지 로드 시 polling 시작
  pollMessages();
});
