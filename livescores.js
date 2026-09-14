document.addEventListener('DOMContentLoaded', () => {
  const options = {
    method: 'GET',
    headers: {
'x-rapidapi-key': '6c522db1damsh73f13b1d1350b6dp1adb3bjsn20d8f083c070',
		'x-rapidapi-host': 'pinnacle-odds.p.rapidapi.com'
  }
};
  fetch('https://pinnacle-odds.p.rapidapi.com/kit/v1/meta-periods?sport_id=1', options)
    .then(response => response.json())
    .then(response => {
      const container = document.getElementById('live-scores');
      console.log(response,response)
      if (response.response.length === 0) {
        container.innerHTML = "<p>No live matches at the moment.</p>";
      } else {
        response.response.forEach(match => {
          const matchInfo = `
            <div class="card" style="margin:10px auto; width:80%;">
              <h3>${match.teams.home.name} vs ${match.teams.away.name}</h3>
              <p>${match.goals.home} - ${match.goals.away}</p>
              <p>Status: ${match.fixture.status.long}</p>
            </div>`;
          container.innerHTML += matchInfo;
        });
      }
    })
    .catch(err => {
      document.getElementById('live-scores').innerHTML = "<p>Error loading live scores.</p>";
      console.error(err);
    });
});
