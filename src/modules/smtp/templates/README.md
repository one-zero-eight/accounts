E-mail clients render HTML differently, do not support some features and have various bugs.

In order to simplify life and achieve maximum compatibility, it was decided to use the open source tool called [MJML](https://github.com/mjmlio/mjml).

---

MJML template for verification code e-mail is at [`verification-code.mjml`](./verification-code.mjml).
It contains text `${{code}}` that should be substituted with the actual verification code.

You can edit the template in the online MJML editor: https://mjml.io/try-it-live.

To generate HTML from the MJML template, you can use this command (NodeJS should be installed):

```sh
npx mjml verification-code.mjml --config.minify -o verification-code.html
```
