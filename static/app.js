const form = document.querySelector('#form')
form.addEventListener('submit', function(e) {
    e.preventDefault()
    getColors()
})

function getColors() {
    const queryData = form.elements.query.value
    fetch('/palette', {
        method: 'POST',
        body: new URLSearchParams({
            query: queryData
        })
    })
    .then((response) => response.json())
    .then(data => {
        console.log(data)
        const colors = data.colors
        const container = document.querySelector('.container')
        createColorBoxes(colors, container)

    })
}

function createColorBoxes(colors, parent){
    parent.replaceChildren()
    for (const color of colors) {
        console.log(color)
        const div = document.createElement('div')
        div.classList.add('color')
        div.style.backgroundColor = color
        div.style.width = `calc(100% / ${colors.length})`

        div.addEventListener('click', function() {
            console.log(color)
            navigator.clipboard.writeText(color)
        })

        const span = document.createElement('span')
        span.innerText = color
        div.appendChild(span)

        parent.appendChild(div)
    }
}