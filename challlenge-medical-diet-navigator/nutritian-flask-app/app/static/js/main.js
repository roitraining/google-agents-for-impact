// Functions to show and hide the modal dialogs used for instructions. 
function showInstructions() {
    document.getElementById("modal-overlay").style.display = "flex";
}

function hideInstructions() {
    document.getElementById("modal-overlay").style.display = "none";
}

function showMarkdownModal(index) {
    const contentDiv = document.getElementById(`markdown-content-${index}`);
    const modalBody = document.getElementById("markdown-modal-body");
    modalBody.textContent = contentDiv.textContent;
    document.getElementById("markdown-modal-overlay").style.display = "flex";
}

function hideMarkdownModal() {
    document.getElementById("markdown-modal-overlay").style.display = "none";
}
