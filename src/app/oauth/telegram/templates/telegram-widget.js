function onTelegramAuth(user) {
    fetch('http://127.0.0.1/auth/telegram/login', {
        method: 'POST', headers: {
            'Content-Type': 'application/json'
        }, body: JSON.stringify(user)
    }).then(function (response) {
        if (response.ok) {
            alert('User is verified');
        } else {
            alert('Error');
        }
    });
}
