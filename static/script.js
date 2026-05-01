 document.addEventListener('DOMContentLoaded', () => {
    const analyzeBtn = document.getElementById('analyze-btn');
    const rewriteBtn = document.getElementById('rewrite-btn');
    const textInput = document.getElementById('text-input');
    const loading = document.getElementById('loading');
    const resultsSection = document.getElementById('results-section');
    const motivationCard = document.getElementById('motivation-card');

    function getIndicatorColor(score) {
        if (score <= 3) return 'var(--color-weak)';
        if (score <= 6) return 'var(--color-moderate)';
        if (score <= 8) return 'var(--color-strong)';
        return 'var(--color-exceptional)';
    }

    async function analyzeText() {
        const text = textInput.value.trim();
        if (!text) {
            alert("Please enter some text before consulting the scale.");
            return;
        }

        analyzeBtn.disabled = true;
        loading.classList.remove('hidden');
        resultsSection.classList.add('hidden');

        try {
            const response = await fetch('/api/analyze', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ text, max_tokens: 1024 })
            });

            const data = await response.json();

            if (response.ok) {
                displayResults(data);
            } else {
                alert("An error occurred: " + (data.error || "Unknown error"));
            }
        } catch (error) {
            alert("Failed to connect to the analysis engine. Ensure your API key is set and server is running.");
            console.error(error);
        } finally {
            analyzeBtn.disabled = false;
            loading.classList.add('hidden');
        }
    }

    function displayResults(data) {
        // Overall Profile
        document.getElementById('overall-profile').textContent = data.overall || "A voice yet to find its form.";

        // Feedback
        // Format feedback nicely
        let feedbackHtml = data.feedback ? data.feedback.replace(/\n/g, '<br>') : "No specific guidance provided.";
        document.getElementById('feedback-text').innerHTML = feedbackHtml;

        // Detection
        document.getElementById('claim-type').textContent = data.claim_type || 'Unknown';
        document.getElementById('generic-density').textContent = data.generic_density || 'Unknown';

        // Dimensions
        let hasWeakArea = false;
        const weakDimensions = [];

        const dimensions = {
            'dim-authenticity': 'AUTHENTICITY',
            'dim-originality': 'ORIGINALITY',
            'dim-emotional_weight': 'EMOTIONAL_WEIGHT',
            'dim-clarity': 'CLARITY',
            'dim-boldness': 'BOLDNESS'
        };

        const dimensionNames = {
            'AUTHENTICITY': 'Authenticity',
            'ORIGINALITY': 'Originality',
            'EMOTIONAL_WEIGHT': 'Emotional Weight',
            'CLARITY': 'Clarity',
            'BOLDNESS': 'Boldness'
        };

        for (const [id, key] of Object.entries(dimensions)) {
            const dimElement = document.getElementById(id);
            const indicator = dimElement.querySelector('.indicator');
            const scoreText = dimElement.querySelector('.score-text');
            const score = data.scores[key] !== undefined ? data.scores[key] : 5; // default moderate if missing

            indicator.style.backgroundColor = getIndicatorColor(score);
            if (scoreText) {
                scoreText.textContent = `${score}/10`;
            }

            if (score <= 4) { // Treat <= 4 as a weak area that needs rewriting motivation
                hasWeakArea = true;
                weakDimensions.push(dimensionNames[key]);
            }
        }

        // Motivation for weak areas
        if (hasWeakArea || data.rewrite_challenge) {
            motivationCard.classList.remove('hidden');
            const weakList = weakDimensions.join(', ');
            document.getElementById('motivation-text').textContent =
                `The great poets took risks. Your verse shows hesitance, particularly in: ${weakList}. ` +
                `Do not settle for the ordinary. Rip it up, bleed on the page, and write it again with true conviction.`;

            let rewriteHtml = data.rewrite_challenge ? data.rewrite_challenge.replace(/\n/g, '<br>') : "No specific rewrite challenge provided.";
            document.getElementById('rewrite-challenge-text').innerHTML = rewriteHtml;
        } else {
            motivationCard.classList.add('hidden');
        }

        resultsSection.classList.remove('hidden');
        resultsSection.scrollIntoView({ behavior: 'smooth' });
    }

    analyzeBtn.addEventListener('click', analyzeText);

    rewriteBtn.addEventListener('click', () => {
        textInput.focus();
        textInput.select();
        window.scrollTo({ top: 0, behavior: 'smooth' });
    });
});
