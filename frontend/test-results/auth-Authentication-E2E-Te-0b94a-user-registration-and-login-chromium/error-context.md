# Page snapshot

```yaml
- generic [active] [ref=e1]:
  - generic [ref=e4]:
    - generic [ref=e5]:
      - heading "Create Account" [level=3] [ref=e6]
      - paragraph [ref=e7]: Enter your information to create your account
    - generic [ref=e8]:
      - generic [ref=e9]:
        - generic [ref=e10]:
          - text: Full Name
          - textbox "Full Name" [ref=e11]:
            - /placeholder: John Doe
        - generic [ref=e12]:
          - text: Email
          - textbox "Email" [ref=e13]:
            - /placeholder: you@example.com
        - generic [ref=e14]:
          - text: Password
          - textbox "Password" [ref=e15]
          - paragraph [ref=e16]: "Must be at least 8 characters and include: uppercase letter, lowercase letter, number, and special character"
      - generic [ref=e17]:
        - button "Create Account" [ref=e18] [cursor=pointer]
        - paragraph [ref=e19]:
          - text: Already have an account?
          - link "Login" [ref=e20] [cursor=pointer]:
            - /url: /login
  - region "Notifications (F8)":
    - list
  - alert [ref=e21]
```