// helper to fetch data and set with React setState hook in functional components


function fetchState (setState, apiUrl) {
    try {
        fetch(apiUrl)
        .then( response => {
            if (!response.ok) { console.log(response) }
            return response.json()
        })
        .then( json => {setState(json)})
    } catch (err) {
      console.error(err.message);
    }
};


function getFetchEffect(setState, apiUrl, period) {
    return () => {
        fetchState(setState, apiUrl)
        let interval = setInterval(() => {fetchState(setState, apiUrl)}, period)
        return function cleanup() {
            clearInterval(interval);
        }
    }
}


export default getFetchEffect;