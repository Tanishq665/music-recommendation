document.getElementById('recommendationForm').addEventListener('submit', function(event) {
    event.preventDefault();
    getRecommendations();
});

async function getRecommendations() {
    const songName = document.getElementById('song_name').value;
    const response = await fetch('/recommend', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ song_name: songName })
    });
    const recommendations = await response.json();
    if (recommendations.error) {
        alert(recommendations.error);
    } else {
        const recommendationsContainer = document.getElementById('recommendations');
        recommendationsContainer.innerHTML = ''; // Clear previous recommendations
        recommendations.forEach(rec => {
            const card = document.createElement('div');
            card.classList.add('recommendation-card');
            card.innerHTML = `
                <h3>${rec['Track Name']}</h3>
                <p>By ${rec['Artists']} from ${rec['Album Name']}</p>
                <p>Release Date: ${rec['Release Date']}</p>
                <p>Popularity: ${rec['Popularity']}</p>
            `;
            recommendationsContainer.appendChild(card);
        });
    }
}
