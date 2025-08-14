// Custom message handlers for WebSocket integration
$(document).on('shiny:connected', function (event) {
  console.log('Shiny connected - WebSocket should be initializing...');
});

// Handle WebSocket refresh requests from Shiny
Shiny.addCustomMessageHandler('websocket_refresh', function (message) {
  if (window.pearlWebSocket && window.pearlWebSocket.isConnected()) {
    window.pearlWebSocket.refresh();
    console.log('WebSocket refresh requested');
  } else {
    console.log('WebSocket not connected, skipping refresh');
  }
});

// Toggle selection highlight for reporting effort selector wrappers
Shiny.addCustomMessageHandler('toggleEffortSelection', function (message) {
  try {
    var el = document.getElementById(message.selector_id);
    if (!el) return;
    if (message.has_selection) el.classList.add('has-selection');
    else el.classList.remove('has-selection');
  } catch (e) {
    console.warn('toggleEffortSelection error', e);
  }
});