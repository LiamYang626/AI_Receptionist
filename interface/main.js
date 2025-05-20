// main.js
$(document).ready(function(){

  // Initialize textillate for the Siri message.
  /*
  $('.siri-message').textillate({
    loop: true,
    sync: true,
    in: { effect: "fadeInLeft", sync: true },
    out: { effect: "fadeOutRight", sync: true }
  });
  $('.siri-message').textillate();
  */
  
  // Initialize SiriWave.
  const siriWave = new SiriWave({
    container: document.getElementById("siri-container"),
    cover: true,
    width: 800,
    height: 200,
    style: "ios9",
    amplitude: 1,
    speed: 0.30,
    autostart: true,
    amplitude: 0.3,   
    speed:     0.1
  });
  siriWave.start();

  let micStream, micCtx;
  const AudioCtx = window.AudioContext || window.webkitAudioContext;

  // Set up audio file analysis once
  const audioP = document.getElementById("audioPlayer");
  let fileCtx, fileAnalyser;
  if (audioP) {
    fileCtx = new AudioCtx();
    fileAnalyser = fileCtx.createAnalyser();
    const approxVisFreq = 5;
    const totalSamplesFile = fileCtx.sampleRate / approxVisFreq;
    fileAnalyser.fftSize = 2 ** Math.floor(Math.log2(totalSamplesFile));

    // Create a single MediaElementSourceNode for the audioPlayer
    const fileSource = fileCtx.createMediaElementSource(audioP);
    fileSource.connect(fileAnalyser);
    fileAnalyser.connect(fileCtx.destination);
  }

  // Visualize live microphone input (client speaking)
  function runAudioVisualizer() {
    navigator.mediaDevices.getUserMedia({ audio: true, video: false })
      .then(stream => {
        micStream = stream;
        micCtx = new AudioCtx();
        const source = micCtx.createMediaStreamSource(stream);
        const analyser = micCtx.createAnalyser();

        // Configure FFT size based on ~5Hz update rate
        const approxVisFreq = 5;
        const totalSamples = micCtx.sampleRate / approxVisFreq;
        analyser.fftSize = 2 ** Math.floor(Math.log2(totalSamples));

        source.connect(analyser);

        const freqData = new Uint8Array(analyser.frequencyBinCount);
        const timeData = new Uint8Array(analyser.frequencyBinCount);

        function updateMicVisual() {
          analyser.getByteTimeDomainData(timeData);
          const amp = timeData.reduce((max, v) => Math.max(max, v), 128) - 128;
          siriWave.setAmplitude((amp / 128) * 10);

          analyser.getByteFrequencyData(freqData);
          let maxBin = 1;
          for (let i = 1; i < freqData.length; i++) {
            if (freqData[i] > freqData[maxBin]) maxBin = i;
          }
          const freq = maxBin * (micCtx.sampleRate / 2) / analyser.frequencyBinCount;
          siriWave.setSpeed(freq / 10000);

          requestAnimationFrame(updateMicVisual);
        }
        updateMicVisual();
      })
      .catch(err => console.error("Audio visualizer error:", err));
  }
  runAudioVisualizer();

  // Visualize assistant's audio file using same analyser
  function runAudioFileVisualizer() {
    // Stop mic visualization
    if (micStream) micStream.getTracks().forEach(t => t.stop());
    if (micCtx) micCtx.close();

    if (!fileAnalyser || !audioP) return;

    siriWave.start();
    const freqData = new Uint8Array(fileAnalyser.frequencyBinCount);
    const timeData = new Uint8Array(fileAnalyser.frequencyBinCount);

    function updateFileVisual() {
      fileAnalyser.getByteTimeDomainData(timeData);
      const amp = timeData.reduce((max, v) => Math.max(max, v), 128) - 128;
      siriWave.setAmplitude((amp / 128) * 10);

      fileAnalyser.getByteFrequencyData(freqData);
      let maxBin = 1;
      for (let i = 1; i < freqData.length; i++) {
        if (freqData[i] > freqData[maxBin]) maxBin = i;
      }
      const freq = maxBin * (fileCtx.sampleRate / 2) / fileAnalyser.frequencyBinCount;
      siriWave.setSpeed(freq / 10000);

      if (!audioP.paused) {
        requestAnimationFrame(updateFileVisual);
      }
    }
    updateFileVisual();
  }

  let currentMessage = "";
  let systemBubble = null;

  function appendChatBubble(role, text){
    if(role === "system"){                          
      if(systemBubble){
          systemBubble.text(text);
          $("#system").text(text);               
      }
      else{
          systemBubble = $("<div/>",{
              "class":"message system loading-text", text
          });
          $("#chat").prepend(systemBubble);
      }
      $("#chat").scrollTop($("#chat")[0].scrollHeight);
      return;                                     
    }
  
    let $bubble;
    if(systemBubble){                               // reuse same row
        $bubble = systemBubble;
        systemBubble = null;                        // it’s now a normal bubble
    }else{
        $bubble = $("<div/>");
        $("#chat").prepend($bubble);
    }

    // configure for the correct side
    if(role === "user"){
        $bubble.attr("class","message user").text(text);
    }else{                                          // assistant
        $bubble.attr("class","message siri").text(text);
    }
    $("#chat").scrollTop($("#chat")[0].scrollHeight);
  }

  async function pollMessages() {
    try {
      const response = await fetch("http://127.0.0.1:5500/message?t=" + Date.now(), { cache: "no-store" });
      if (!response.ok) {
        console.error("HTTP error:", response.status);
        setTimeout(pollMessages, 1000);
        return;
      }
      const data = await response.json();
      const message = data.role + "|" + data.content;
      if (message !== currentMessage){
        console.log("Received message:", data.content);
        appendChatBubble(data.role, data.content);
        currentMessage = message;
        if(data.role === "assistant") {
          let audioPlayer = document.getElementById("audioPlayer");
          if (audioPlayer) {
            audioPlayer.src = "http://127.0.0.1:5500/audio?t=" + Date.now();
            audioPlayer.play()
              .then(() => runAudioFileVisualizer(audioPlayer))
              .catch(e => console.error("Audio play error:", e));
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
      .then(() => runAudioVisualizer())
      .catch(error => console.error("Error sending audio finished signal:", error));
    });
  }

  // 페이지 로드 시 polling 시작
  pollMessages();
});
