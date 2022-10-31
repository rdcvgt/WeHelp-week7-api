document.querySelector('.userNameBtn').addEventListener('click', () => {
    //清除顯示的資訊
    if (document.querySelector('.showData')) {
        document.querySelector('.showData').remove()
    }
    //拿取輸入資料並 fetch
    username = (document.querySelector('.userNameInput').value)
    url = "/api/member?username=" + username
    fetch(url, {
            method: 'GET'
        })
        .then(res => res.json())
        .then(data => userData(data))
        .catch(err => {
            wrongName(err)
        })
})
//成功拿到資料
function userData(data) {
    name = data.data.name
    username = data.data.username
    let span = document.createElement("span")
    span.classList.add('showData')
    span.append(
        `${name}(${username})`
    )
    document.querySelector('.searchName').append(span)
}
//當拿到資料爲空值，會透過 catch 呼叫此函式
function wrongName(err) {
    let span = document.createElement("span")
    span.classList.add('showData')
    span.append("查無資料")
    document.querySelector('.searchName').append(span)
}