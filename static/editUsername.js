document.querySelector('.editUserNameBtn').addEventListener('click', () => {
    //清除顯示的資訊
    if (document.querySelector('.showResult')) {
        document.querySelector('.showResult').remove()
    }
    //拿取輸入資料並 fetch
    newName = document.querySelector('.editUserNameInput').value
    username = document.querySelector('.passUsername').value
    url = "/api/member?username=" + username
    fetch(url, {
            method: 'PATCH',
            body: JSON.stringify({
                "name": newName
            }),
            headers: {
                'content-type': 'application/json'
            }
        })
        .then(res => res.json())
        .then(data => status(data))
        .catch(err => {
            wrong(err)
        })
})
//成功拿到資料
function status(data) {
    let span = document.createElement("span")
    span.classList.add('showResult')
    if (data.ok) {
        span.append("更新成功")
    } else {
        span.append("與目前名稱相同")
    }

    document.querySelector('.editName').append(span)

}
//當拿到資料爲空值，會透過 catch 呼叫此函式
function wrong(err) {
    let span = document.createElement("span")
    span.classList.add('showResult')
    span.append("更新失敗")
    document.querySelector('.editName').append(span)
}