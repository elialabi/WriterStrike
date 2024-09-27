function showUserLoading() {
    console.log("Showing user loading overlay");
    document.getElementById('user-loading').style.display = 'flex';
}

function showAILoading() {
    console.log("Showing AI loading overlay");
    document.getElementById('ai-loading').style.display = 'flex';
}

function hideLoading() {
    console.log("Hiding loading overlays");
    document.getElementById('user-loading').style.display = 'none';
    document.getElementById('ai-loading').style.display = 'none';
}

function analyzeScene(sceneId) {
    console.log("Analyzing scene:", sceneId);
    showAILoading();
    fetch(`/analyze_scene/${sceneId}`, {
        method: 'POST',
    })
    .then(response => response.json())
    .then(data => {
        console.log("Analysis complete:", data);
        hideLoading();
        // Handle the response data
    })
    .catch(error => {
        console.error('Error:', error);
        hideLoading();
    });
}
