function saveLoadData() {
    let state = document.getElementById('state_id').value; // check unga input id
    let amount = document.getElementById('amount_id').value; 

    // Table Update logic
    let table = document.getElementById('loadTableBody');
    let row = `<tr><td>${state}</td><td>₹ ${amount}</td></tr>`;
    table.innerHTML += row;

    // Voice Confirmation logic
    let msg = new SpeechSynthesisUtterance(state + " data saved");
    window.speechSynthesis.speak(msg);
}