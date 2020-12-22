$(function () {

  $("#messages").on("click", "button", async function (e) {
    e.preventDefault();

    let message_id = e.currentTarget.id;
    let response = await axios.post(`/messages/${message_id}/like`)
    if (response.status == 200) {
      $(e.currentTarget).toggleClass("btn-primary btn-secondary");
    } else {
      console.log(response.data.message);
    }
  })
  

  $('#message-submit').on('click', async e => {
    e.preventDefault();
    $('#message-modal').modal('toggle');
    let text = $('#text').val();
    let response = await axios.post('/messages/new', { text });

    // we were going to prepend the user/message info
  });

 

});