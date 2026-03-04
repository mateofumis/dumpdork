# **DumpDork API Setup Guide**

This guide will help you obtain the necessary API keys and tokens to use with **DumpDork**.

## **1. Google & Brave (RapidAPI)**

Both Google and Brave search providers in this tool are powered by **RapidAPI**.

1. **Create an Account:** Go to [RapidAPI.com](https://rapidapi.com/auth/sign-up) and sign up.  
2. **Subscribe to the APIs:**  
   * **Google:** Go to the [Google Search74 API](https://rapidapi.com/herosAPI/api/google-search74/playground) page.  
   * **Brave:** Go to the [Brave Web Search API](https://rapidapi.com/rainapi-rainapi-default/api/brave-web-search/playground/) page.  
3. **Select a Plan:** Both offer a "Basic" (Free) tier with a limited number of requests per month.  
4. **Get Your Key:** Once subscribed, go to the "Endpoints" tab in the RapidAPI playground. Look for the `x-rapidapi-key` header in the code snippets. This key is the same for all APIs on your RapidAPI account.

## **2. GitHub (Personal Access Token)**

The GitHub provider uses official GitHub APIs. While it can work without a token for very limited requests, a token is highly recommended to avoid rate limits.

1. **Log in to GitHub:** Go to [GitHub.com](https://github.com/).  
2. **Settings:** Click your profile picture -> **Settings**.  
3. **Developer Settings:** On the left sidebar, click **Developer settings** (at the bottom).  
4. **Personal Access Tokens:** Click **Tokens (classic)**.  
5. **Generate Token:** Click **Generate new token (classic)**.  
6. **Scopes:** For dorking public repositories, you don't need to select any specific scopes. If you want to dork your private repositories, select repo.  
7. **Copy Token:** Copy the token immediately. You won't be able to see it again.

## **3. Configuring DumpDork**

Once you have your keys, run the DumpDork setup wizard:

```bash
python3 dumpdork.py -w
```

The wizard will prompt you for each key.

* **RapidAPI Key:** Enter your key when prompted for Google and Brave.  
* **GitHub Token:** Paste your Personal Access Token when prompted for GitHub.

### **Manual Configuration**

If you prefer to edit the file manually, the configuration is stored in YAML format at:

```
~/.config/dumpdork/config.yaml
```

Example structure:

```yaml
rapidapi:  
  host: google-search74.p.rapidapi.com  
  keys:  
    google: "your_rapidapi_key_here"  
    brave: "your_rapidapi_key_here"  
    github: "your_github_token_here"  
```
