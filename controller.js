//darkevil make this, with passion and a great hope while listening metal and hard rock!!

const getUrl = 'http://ec2-34-212-201-251.us-west-2.compute.amazonaws.com:8089/help';
const askAnotherUrl = 'http://ec2-34-212-201-251.us-west-2.compute.amazonaws.com:8089/help/another';
const markUrl = 'http://ec2-34-212-201-251.us-west-2.compute.amazonaws.com:8089/help/mark';

const input_ids = []

for (var i = 1; i < 13; i++) {
    input_ids.push('e' + i);
}

let unwanted_tweets = [];
let actual_tweet_id = '';

function getTweet() {
    fetch(getUrl).then(data => { return data.json() }).then(res => processBackResponse(res));
}

function processBackResponse(response) {
    document.getElementById("tweet_text").innerHTML = response.text;
    actual_tweet_id = response.id;
}

function askAnotherTweet() {
    unwanted_tweets.push(String(actual_tweet_id));
    const request = JSON.stringify({ 'ids': unwanted_tweets });
    fetch(askAnotherUrl, {
        method: "POST",
        body: request,
        headers: {
            "Content-Type": "application/json"
        }
    }).then(data => { return data.json() }).then(res => processBackResponse(res));
}

function buildRequest() {
    const entityList = [];
    for (id of input_ids) {
        let inputValue = document.getElementById(id).value;
        if (inputValue) {
            selectValue = document.getElementById(id + 'i').value;
            const entity = { 'type': selectValue, 'text': inputValue.trim() };
            entityList.push(entity);
        }
    }
    return entityList;
}

function markTweet() {
    const entityList = buildRequest();

    if (entityList.length > 0) {

        //Disable button
        document.getElementById('change_btn').disabled = true;
        document.getElementById('train_btn').disabled = true;

        let defender = document.getElementById('defender').value;

        request = { 'id': actual_tweet_id, 'entities': entityList, 'defender':defender.trim() };
        fetch(markUrl, {
            method: "POST",
            body: JSON.stringify(request),
            headers: {
                "Content-Type": "application/json"
            }
        }).then(data => data).then(res => location.reload());
    }
}

getTweet();