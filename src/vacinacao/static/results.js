function createColumns(result, row) {
  for (let field in result) {
    let col = document.createElement("td");
    let text = document.createTextNode(result[field])
    col.appendChild(text)
    row.appendChild(col)
  }
}

function createRows(response) {
  const resultsBody = document.getElementById('results')
  response.forEach(function (result) {
    var row = document.createElement("tr");
    createColumns(result, row)
    resultsBody.appendChild(row)
  })
}

function removeResults(elementId) {
  const results = document.getElementById(elementId);
  while (results.firstChild) {
    results.removeChild(results.lastChild);
  }
}

function sanitize(name) {
  name = name.replace(/[0-9]/g, '')
  name = name.normalize("NFD").replace(/[\u0300-\u036f]/g, "")
  name = name.replace(/[`~!@#$%^&*()_|+\-=?;:'",.<>\{\}\[\]\\\/]/gi, '')
  return name.trim()
}

function toggleDisplays(results) {
  if (results.length === 0) {
    // Show message for 'No results found', hide result table
    document.getElementById('not-found').style.display = ''
    document.getElementById('results-table').style.display = 'none'
  } else {
    // Show result table, hide 'No results found' message
    document.getElementById('not-found').style.display = 'none'
    document.getElementById('results-table').style.display = ''
  }
}

function submitName(event) {
  event.preventDefault();

  const noInputWarning = document.getElementById('no-input-warning');
  const nameInput = document.getElementById('name');

  let name = sanitize(nameInput.value);  // Get rid of accents, numbers and symbols
  if (!name) {
    noInputWarning.style.display = '';
    return;
  } else {
    noInputWarning.style.display = 'none';
  }

  postData('/search', {name: nameInput.value})
    .then(results => {
        noInputWarning.style.display = 'none';
        removeResults('results');  // Remove to display a new one
        toggleDisplays(results);
        createRows(results);
      }
    )
}

document.getElementById('search').addEventListener('click', submitName)
document.getElementById('name-form').addEventListener('submit', submitName)
