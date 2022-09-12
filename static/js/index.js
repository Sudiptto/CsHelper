function deleteEvent(noteId) {
    fetch("/delete-event", {
      method: "POST",
      body: JSON.stringify({ noteId: noteId }),
    }).then((_res) => {
      window.location.href = "/meets";
    });
  }