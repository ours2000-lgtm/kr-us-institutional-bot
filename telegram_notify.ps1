param(
    [string]$Message = "알림 없음"
)

$botToken = "YOUR_TELEGRAM_BOT_TOKEN"
$chatId   = "YOUR_CHAT_ID"

$encoded = [System.Web.HttpUtility]::UrlEncode($Message)
$url = "https://api.telegram.org/bot$botToken/sendMessage?chat_id=$chatId&text=$encoded"

Invoke-WebRequest -Uri $url -UseBasicParsing | Out-Null
