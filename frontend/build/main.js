const root = document.getElementById('root');
root.innerHTML = `
  <h1>🎬 Movie Matcher</h1>
  <input type="text" id="search" placeholder="Enter a search term..." />
  <button id="go">Find Matches</button>
  <pre id="results">Results will appear here</pre>
`;

document.getElementById('go').onclick = async () => {
  const searchTerm = document.getElementById('search').value;
  const resEl = document.getElementById('results');
  resEl.textContent = 'Searching...';

  try {
    const response = await fetch('/match-movies', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ searchTerm }),
    });

    const data = await response.json();
    if (data.matches && data.matches.length > 0) {
      resEl.textContent = data.matches.map(m => `🎥 ${m.title}: ${m.reason}`).join('\n\n');
    } else {
      resEl.textContent = 'No strong matches found.';
    }
  } catch (err) {
    resEl.textContent = 'Error fetching matches.';
    console.error(err);
  }
};
