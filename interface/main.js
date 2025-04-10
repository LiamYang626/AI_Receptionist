// main.js
$(document).ready(function(){

  // Initialize SiriWave.
  var siriWave = new SiriWave({
    container: document.getElementById("siri-container"),
    width: 800,
    height: 200,
    style: "ios9",
    amplitude: 1,
    speed: 0.30,
    autostart: true
  });

  // Initialize textillate for the Siri message.
  $('.siri-message').textillate({
    loop: true,
    sync: true,
    in: { effect: "fadeInUp", sync: true },
    out: { effect: "fadeOutUp", sync: true }
  });

  let currentMessage = "";

  updateUI("Initializing...");

  async function pollMessages() {
    try {
      const response = await fetch("http://127.0.0.1:5500/message");
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
      }
      let audioPlayer = document.getElementById("audioPlayer");
      if (audioPlayer) {
        // URL에 타임스탬프를 덧붙여 캐시를 피합니다.
        audioPlayer.src = "http://127.0.0.1:5500/audio";
        // 오디오 자동 재생 (브라우저 정책에 따라 auto play가 안 될 수도 있으므로, play() 호출)
        audioPlayer.play().catch(e => console.error("Audio play error:", e));
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

  // 페이지 로드 시 polling 시작
  pollMessages();
});
