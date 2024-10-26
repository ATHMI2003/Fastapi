// Function to handle text summarization
document.getElementById("summarize-form").addEventListener("submit", async (event) => {
    event.preventDefault(); // Prevent default form submission

    const text = document.getElementById("text").value;
    const summaryRatio = parseFloat(document.getElementById("summary_ratio").value);
    
    if (!text || isNaN(summaryRatio)) {
        displayError("Please provide valid text and summary ratio.");
        return;
    }

    const response = await fetch("/summarize", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ text, summary_ratio: summaryRatio })
    });

    const data = await response.json();
    
    if (data.summary) {
        document.getElementById("summary").innerText = data.summary;
        document.getElementById("summary").style.color = "#5cb85c"; // Dark green for success
        clearError();
    } else {
        displayError("Error summarizing text.");
    }
});

// Function to handle audio trimming
document.getElementById("trim-form").addEventListener("submit", async (event) => {
    event.preventDefault(); // Prevent default form submission

    const formData = new FormData(event.target);
    
    const response = await fetch("/trim-audio", {
        method: "POST",
        body: formData
    });

    const data = await response.json();
    
    // Display trimmed audio
    if (data.trimmed_audio_url) {
        document.getElementById("audio-player").innerHTML = `
            <audio controls>
                <source src="${data.trimmed_audio_url}" type="audio/wav">
                Your browser does not support the audio tag.
            </audio>
        `;
        clearError();
    } else {
        displayError("Error trimming audio.");
    }
});

// Function to handle image resizing
document.getElementById("resize-form").addEventListener("submit", async (event) => {
    event.preventDefault(); // Prevent default form submission

    const formData = new FormData(event.target);

    const response = await fetch("/resize-image", {
        method: "POST",
        body: formData
    });

    const data = await response.json();
    
    // Display resized image
    if (data.resized_image_url) {
        document.getElementById("image-display").innerHTML = `
            <img src="${data.resized_image_url}" alt="Resized Image" style="max-width: 100%; height: auto;">
        `;
        clearError();
    } else {
        displayError("Error resizing image.");
    }
});

// Function to display error messages
function displayError(message) {
    const errorElement = document.createElement("div");
    errorElement.id = "error-message";
    errorElement.innerText = message;
    errorElement.style.color = "#d9534f"; // Red color for error
    document.body.appendChild(errorElement);
}

// Function to clear error messages
function clearError() {
    const errorElement = document.getElementById("error-message");
    if (errorElement) {
        errorElement.remove();
    }
}
