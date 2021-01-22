function makeRequest(url, payload=null, onreadystatechangeFunction=null){
    let xhr = new XMLHttpRequest();

    if (onreadystatechangeFunction){ xhr.onreadystatechange = onreadystatechangeFunction; }
    
    xhr.open("POST", url);

    if (payload){
        xhr.send(payload);
    }

    else{
        xhr.send();
    }
}