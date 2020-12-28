"use strict";

function getToggleLikeAPI(msgId) {
  return `/api/messages/${msgId}/toggle_like`
}

async function toggleLike(evt) {
  let icon = $(evt.target);
  let msgId = icon.data("msg-id");
  const API = getToggleLikeAPI(msgId);
  let resp = await axios.post(API)

  if (resp.data.message === "Bad like" || resp.status === 401) {
    return;
  }

  icon.toggleClass("far");
  icon.toggleClass("fas");
}

$("#messages").on("click", ".fa-heart", toggleLike);