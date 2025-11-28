# Page snapshot

```yaml
- generic [active] [ref=e1]:
  - generic [ref=e4]:
    - generic [ref=e5]:
      - heading "Login" [level=3] [ref=e6]
      - paragraph [ref=e7]: Enter your email and password to access your account
    - generic [ref=e8]:
      - generic [ref=e9]:
        - generic [ref=e10]:
          - text: Email
          - textbox "Email" [ref=e11]:
            - /placeholder: you@example.com
        - generic [ref=e12]:
          - text: Password
          - textbox "Password" [ref=e13]
      - generic [ref=e14]:
        - button "Login" [ref=e15] [cursor=pointer]
        - paragraph [ref=e16]:
          - text: Don't have an account?
          - link "Register" [ref=e17] [cursor=pointer]:
            - /url: /register
  - region "Notifications (F8)":
    - list
  - alert [ref=e18]
```