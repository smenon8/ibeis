$("body").keydown(function(event) {
  key = event.which;
  console.log(key);
  if(key == 13)
  {
    // Enter key pressed, submit form as accept
    $('input#turk-submit-accept').click();
  }
  else if(key == 32)
  {
    // Space key pressed, submit form as delete
    $('input#turk-submit-clear').click();
  }
});