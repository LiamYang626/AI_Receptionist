// main.js
$(document).ready(function(){
  // Initialize textillate for the main text element.
  $('.tlt').textillate({
    loop: true,
    sync: true,
    in: { effect: "bounceIn" },
    out: { effect: "bounceOut" }
  });

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

  // Establish a WebSocket connection with the FastAPI server.
  const ws = new WebSocket("ws://localhost:5500/ws");

  ws.onopen = function() {
    console.log("WebSocket connected.");
  };

  ws.onmessage = function(event) {
    const message = JSON.parse(event.data);
    console.log("Received message:", message);
    // Update the UI based on the action.
    if(message.action === "DisplayText") {
      $('.text-light.tlt.text-center').replaceWith(message.text);
      $('.text-light.tlt.text-center').textillate('start');
    } else if(message.action === "DisplayMessage") {
      $(".siri-message").replaceWith(message.text);
      $('.siri-message').textillate('start');
    } else if(message.action === "senderText") {
      var chatBox = document.getElementById("chat-canvas-body");
      chatBox.innerHTML += `<div class="row justify-content-end mb-4">
        <div class="width-size">
          <div class="sender_message">${message.text}</div>
        </div>
      </div>`;
      chatBox.scrollTop = chatBox.scrollHeight;
    } else if(message.action === "receiverText") {
      var chatBox = document.getElementById("chat-canvas-body");
      chatBox.innerHTML += `<div class="row justify-content-start mb-4">
        <div class="width-size">
          <div class="receiver_message">${message.text}</div>
        </div>
      </div>`;
      chatBox.scrollTop = chatBox.scrollHeight;
    }
  };

  ws.onclose = function() {
    console.log("WebSocket connection closed.");
  };

  // Mic button: switch UI to voice mode.
  $("#MicBtn").click(function(){
    $("#Oval").attr("hidden", true);
    $("#SiriWave").attr("hidden", false);
    // Optionally send a command via ws.send() if needed.
  });

  // Send button: send user message.
  $("#SendBtn").click(function(){
    let userMessage = $("#chatbox").val();
    if(userMessage.trim()){
      ws.send(JSON.stringify({"action": "userMessage", "text": userMessage}));
      $("#chatbox").val('');
    }
  });

  // Toggle Send/Mic buttons based on text input.
  $("#chatbox").on('keyup', function(){
    let message = $(this).val();
    if(message.length === 0){
      $("#MicBtn").attr('hidden', false);
      $("#SendBtn").attr('hidden', true);
    } else {
      $("#MicBtn").attr('hidden', true);
      $("#SendBtn").attr('hidden', false);
    }
  });

  // Allow sending message on Enter key.
  $("#chatbox").keypress(function(e){
    if(e.which === 13){
      $("#SendBtn").click();
    }
  });
});
