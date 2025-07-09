import asyncio
from typing import Dict

from fastapi import Depends

from system.src.app.config.settings import settings
from system.src.app.usecases.categorisation_usecase.categorisation_usecase import (
    CategorizationUsecase,
)
from system.src.app.usecases.generate_drafts_usecases.generate_drafts_usecase import (
    GenerateDraftsUsecase,
)
from system.src.app.usecases.query_docs_usecases.query_docs_usecase import (
    QueryDocsUsecase,
)


class GenerateDraftsController:

    def __init__(
        self,
        generate_drafts_usecase: GenerateDraftsUsecase = Depends(
            GenerateDraftsUsecase
        ),
        query_docs_usecase: QueryDocsUsecase = Depends(QueryDocsUsecase),
        categorization_usecase: CategorizationUsecase = Depends(
            CategorizationUsecase
        ),
    ):
        self.generate_drafts_usecase = generate_drafts_usecase
        self.query_docs_usecase = query_docs_usecase
        self.categorization_usecase = categorization_usecase

    async def generate_drafts(self, query: Dict):

        # categorization_response = await self.categorization_usecase.execute(query)

        # rocket_docs_query = categorization_response.get("doc_search_query")
        # dataset_query = f"Subject: {categorization_response.get('subject')}\n{categorization_response.get('body')}"
        # categories = categorization_response.get("categories")

        # # Prepare search tasks, but only if the required data is present
        # tasks = []
        
        # # Check if rocket_docs_query is present and not empty
        # if rocket_docs_query and rocket_docs_query.strip():
        #     rocket_docs_task = self.query_docs_usecase.query_docs(
        #         rocket_docs_query, settings.ROCKET_DOCS_PINECONE_INDEX_NAME
        #     )
        #     tasks.append(("rocket_docs", rocket_docs_task))
        # else:
        #     print("Skipping rocket docs search - empty or missing doc_search_query")
            
        # # Check if categories are present and not empty
        # if categories and len(categories) > 0:
        #     dataset_task = self.query_docs_usecase.query_docs(
        #         dataset_query, settings.PINECONE_INDEX_NAME, categories=categories
        #     )
        #     tasks.append(("dataset", dataset_task))
        # else:
        #     print("Skipping dataset search - empty or missing categories")

        # # Execute available tasks
        # results = {}
        # if tasks:
        #     # Execute only the available tasks
        #     task_names = [task[0] for task in tasks]
        #     task_coroutines = [task[1] for task in tasks]
        #     task_results = await asyncio.gather(*task_coroutines)
            
        #     # Map results back to their names
        #     for name, result in zip(task_names, task_results):
        #         results[name] = result
        
        # # Get results or empty lists if tasks were skipped
        # rocket_docs_response = results.get("rocket_docs", [])
        # dataset_response = results.get("dataset", [])

        # generate_drafts_query = {
        #     "from": categorization_response.get("from"),
        #     "subject": categorization_response.get("subject"),
        #     "body": categorization_response.get("body"),
        #     "rocket_docs_response": rocket_docs_response,
        #     "dataset_response": dataset_response,
        #     "categories": categories if categories else [],  # Ensure categories is always a list
        #     "attachments": query.get("attachments", []),  # Pass attachments from original query
        # }
        generate_drafts_query = {
            "from": "customer.urgent@company.com",
            "subject": "Critical Platform Issues - Urgent Support Needed",
            "body": """
Dear Rocket Support Team,

We are experiencing critical issues that require immediate attention:

1. PAYMENT PROCESSING: Our subscription payment failed multiple times despite valid payment methods. This is blocking our team from accessing premium features.

2. TOKEN CONSUMPTION: The platform is consuming tokens at an alarming rate without producing usable results. We've lost over 2M tokens in failed generations.

3. DEPLOYMENT ISSUES: Generated applications fail to deploy properly with multiple runtime errors that weren't present in previews.

4. PERFORMANCE DEGRADATION: The platform response time has significantly decreased, affecting our development timeline.

This is severely impacting our business operations and client deliveries. We need:
- Immediate payment issue resolution
- Token refund for failed generations  
- Technical assistance for deployment
- Performance optimization

Please treat this as PRIORITY 1 and provide comprehensive assistance.

Business Impact: HIGH
Urgency: CRITICAL
Expected Response Time: Within 2 hours

Best regards,
Sarah Johnson
CTO, TechFlow Solutions
sarah.johnson@techflow.com
+1-555-0199
        """,
            "rocket_docs_response": [
            {
                "query": "\n# Pricing plans\n\n> Here's everything you need to know about how our pricing works and which plan fits your needs.\n\n\t...\n\n| Plan         | Price       | Tokens/month        | Figma-to-code    | Bonus Tokens | Refuels Available |\n| :----------- | :---------- | :------------------ | :--------------- | :----------- | :---------------- |\n| **Free**     | \\$0         | 2M (1M each week)   | 2 screen         | –            | No                |\n| **Personal** | \\$25/month  | 5M                  | Up to 6 screens  | –            | Yes               |\n| **Rocket**   | \\$50/month  | 10.5M (incl. bonus) | Up to 12 screens | 500K         | Yes               |\n| **Booster**  | \\$100/month | 22M (incl. bonus)   | Up to 25 screens | 2M           | Yes               |\n",
                "relevance_score": 0.7890625,
                "metadata": {
                    "content_hash": "d64e862b2d0f3dfdf0df9fa3b1c495b2ab3e9cbb018cff584a6963ac71644234",
                    "end_index": 6916,
                    "start_index": 6152,
                    "token_count": 764,
                    "url": "https://docs.rocket.new/get-started/pricing-plans"
                }
            },
            {
                "query": "\n### <Icon icon=\"sparkles\" color=\"currentcolor\" size={23} /> Free plan – Try before you fly\n\n<Info>\n  <b>What’s something you’ve always wanted to build, but never got around to?</b>\\\n  Maybe a simple to-do app, a landing page, or a personal blog. Just type it and see what Rocket creates.\n</Info>\n\n**What’s included:**\n\n* **One-time token credit:** 2M total tokens, with a 1M weekly usage limit. Unused weekly tokens expire and don’t roll over.\n* **Use your tokens for:**\n  * **Natural language chat**: Play around with your ideas - no commitment, just creativity. Try it, tweak it, love it, and buy when you're ready.\n  * **Figma-to-code**: Convert 2 screens for free into a responsive, production-ready app.\n\n<Note>\n  <b>Token tip:</b>\\\n  Simple prompts like *“Make a login screen”* use fewer tokens. Complex dashboards use more.\n</Note>\n\n<Tip>\n  <b>Best for:</b>\n\n  * Exploring Rocket’s interface\n  * Previewing output quality\n  * Understanding token behavior\n\n  <b>Try this:</b>\\\n  Ask for something bold - Rocket thrives on creativity.\n</Tip>\n\n***\n\n### <Icon icon=\"user\" color=\"currentcolor\" size={23} /> Personal Plan – \\$25/month\n\n**Ideal for light, exploratory use.**\\\nPerfect for solo creators building portfolios, landing pages, and personal tools.\n\n**What’s included:**\n\n* **Monthly token credit:** 5M\n* **Natural language chat**\n* **Figma-to-code:** Convert up to 6 screens per month\n* **Use refuels anytime** if you need more tokens mid-cycle\n\n<Tip>\n  <b>Best for:</b>\n\n  * Portfolios or digital resumes\n  * One-pagers, forms, blogs\n  * Personal landing pages\n</Tip>\n\n***\n\n### <Icon icon=\"rocket\" color=\"currentcolor\" size={23} /> Rocket Plan – \\$50/month\n\n**Most popular – For pros using Rocket weekly.**\\\nConsistent token power to prototype, test, and build at speed.\n\n**What’s included:**\n\n* **Monthly token credit:** 10M\n* **Bonus tokens:** 500K/month\n* **Figma-to-code:** Up to 12 screens\n* **Refuels available** anytime via subscription modal\n\n<Tip>\n  <b>Best for:</b>\n\n  * MVPs and client dashboards\n  * Admin panels with roles\n  * Marketing sites and SaaS prototypes\n</Tip>\n\n***\n\n### <Icon icon=\"rocket-launch\" color=\"currentcolor\" size={23} /> Booster Plan – \\$100/month\n\n**Built for high-volume, high-output users.**\\\nGreat for teams, platforms, and full-stack app flows.\n\n**What’s included:**\n\n* **Monthly token credit:** 20M\n* **Bonus tokens:** 2M/month\n* **Figma-to-code:** Up to 25 screens\n* **Refuels supported** for large bursts or last-minute changes\n\n<Tip>\n  <b>Best for:</b>\n\n  * Full SaaS systems\n  * E-commerce & subscriptions\n  * Complex, multi-screen apps\n</Tip>\n\n***\n\n",
                "relevance_score": 0.75390625,
                "metadata": {
                    "content_hash": "a98de0d9701b1619a8a7e6b6bbfdf99b1c34b01bc1bb500a5dbb66ab9a136ea8",
                    "end_index": 6012,
                    "start_index": 3407,
                    "token_count": 2605,
                    "url": "https://docs.rocket.new/get-started/pricing-plans"
                }
            },
            {
                "query": "\n# Pricing plans\n\n> Here's everything you need to know about how our pricing works and which plan fits your needs.\n\n\t...\n\n**Tokens are Rocket’s in-app currency – think of them as the fuel for your app-building journey.**\\\nEvery time you generate an app from a Figma design or describe an idea in natural language, tokens are used to process and deliver results. The more complex your request, the more tokens it takes.\n",
                "relevance_score": 0.69921875,
                "metadata": {
                    "content_hash": "719f2bf4b802efc05016015d40befe4b01956acd57b6caab35153319964192af",
                    "end_index": 676,
                    "start_index": 257,
                    "token_count": 419,
                    "url": "https://docs.rocket.new/get-started/pricing-plans"
                }
            },
            {
                "query": "\n# Pricing plans\n\n> Here's everything you need to know about how our pricing works and which plan fits your needs.\n\n\t...\n\n<Tip>\n  <b>Need Help?</b>\\\n  Unsure which path to take?\\\n  [Reach out to support](mailto:support@rocket.new) - we’ll help you choose confidently.\n</Tip>\n",
                "relevance_score": 0.64453125,
                "metadata": {
                    "content_hash": "237430d8b24e65b786584ac487df55c0bcb558ebe120397a5a1e32e0df74c25a",
                    "end_index": 13861,
                    "start_index": 13586,
                    "token_count": 275,
                    "url": "https://docs.rocket.new/get-started/pricing-plans"
                }
            },
            {
                "query": "\n# Pricing plans\n\n> Here's everything you need to know about how our pricing works and which plan fits your needs.\n\n\t...\n\nLaunch your first project in minutes.\\\nStart here → [rocket.new](https://rocket.new)\n",
                "relevance_score": 0.6328125,
                "metadata": {
                    "content_hash": "99bfe56c9e9060bd93ff8707bb5392288b64c40c06772f6ec43f0902db8664a1",
                    "end_index": 13586,
                    "start_index": 13379,
                    "token_count": 207,
                    "url": "https://docs.rocket.new/get-started/pricing-plans"
                }
            }
        ],
            "dataset_response": [
            {
                "query": "Hi Rocket,\n\nI just signed up to your service yesterday to explore your tool. It seems pretty powerful so far, but I am very disappointed by the token usage. \n\nTried to fix your React minified issues, and it meaninglessly used up 1M of tokens 3x.\n\nCan I regain those unfairly lost tokens please?\n\nAppreciate hearing back from you.\n\nSincerely, \nEvy Lee",
                "relevance_score": 0.59375,
                "metadata": {
                    "categories": [
                        "token_economy_credit_systems"
                    ],
                    "from": "evy.leeyiwen@gmail.com",
                    "response": "Hey Evy,\n\nKalpesh, this side. Thank you for reaching out and giving Rocket a try.\n\nI understand your concern, and we are working actively to address this\nissue. For now, I have added 3M tokens back to your account.",
                    "subject": "Small errors using up 3M tokens"
                }
            },
            {
                "query": "Dear Rocket Support Team,\n\nI recently started using your platform and appreciate the potential it\noffers. However, I’ve encountered a recurring issue where the AI makes\nmistakes that I need to correct, which unfortunately consumes a significant\nnumber of tokens. I’ve already used up over 10 million tokens primarily on\nfixing these errors.\n\nThe service performs well during the first half of a project, but\nafterward, the quality tends to drop, making it less efficient and more\ncostly.\n\nDespite this, I’m still very interested in continuing with Rocket and even\nupgrading to the next level. Given the challenges I’ve experienced, I’d\ngreatly appreciate it if you could provide a discount code to help offset\nsome of these costs.\n\nThank you for your time and consideration.\n\nKind regards,\n\nBill",
                "relevance_score": 0.58203125,
                "metadata": {
                    "categories": [
                        "token_economy_credit_systems",
                        "ai_performance_quality"
                    ],
                    "from": "a.bilguunzorigt@gmail.com",
                    "response": "Hey Bilguunzorigt,\n\nThank you for reaching out, and I understand the issue you are facing. I\nhave reviewed them and agree with what you are saying. There was some\nissues with Supabase and the chat. We have pushed a new release today, and\nnow you'll not face such problems.\n\nAs a next step; you can do the following:\n1. Please delete all the projects and start fresh. I have added 5M tokens\nto your account.\n2. Here's a 30% off code for your next purchase: BA300FF (You can use it\nfor the upgrade plan or purchase refuel tokens)\n\nI hope this will offset your overall loss. Let me know if you have any\nquestions.",
                    "subject": "Request"
                }
            },
            {
                "query": "Dear Rocket Support Team,\n\nI hope this message finds you well.\n\nAfter a week of using your AI assistant, I want to start by expressing my\ndeep appreciation for what you’ve built. Rocket AI represents a major leap\ntoward the future of software development. The concept of an AI that can\ngenerate, structure, and even link code components to produce a working app\nis not just powerful—it’s transformative. Your platform shows immense\npotential, and I truly believe it can redefine how developers work.\n\nThat said, I’m reaching out today with a serious concern.\n\nDespite my enthusiasm, I’ve now spent over 7 million tokens trying to\nresolve a very basic issue: simply setting the correct manager username and\npasscode so I can access my app. The AI tries hard to fix it, but each\nattempt fails or loops back with the same error. As a result, the tokens\nwere consumed with no real progress—and no working login functionality.\n\nThis was not a complex task. I wasn’t trying to build a new feature—I just\nneeded the working credentials in place. The system kept suggesting fixes,\nbut nothing worked, and all I could do was watch my tokens drain.\n\nAs you can verify from our conversation logs, the last 7 million tokens\nwere entirely spent on this unresolved issue. Moreover, I have spent a\ntotal of 25 million tokens, out of which at least 15 million were wasted on\nunsuccessful fixes and non-functional builds.\n\nThis has been very frustrating, especially as a developer who truly\nbelieved in this tool. If the AI is capable of generating a full\napp—including the main.dart, the pubspec.yaml, imports, and database\nlinks—then it shouldn’t fall short on something as essential as a working\nlogin gate.\n\nNow I’m hesitant to refuel, as I don’t know if the same will happen again.\nI believe in Rocket, but I need reassurance that these issues are being\ntaken seriously, and that there’s a safeguard for users who lose large\nnumbers of tokens without results.\n\nI kindly ask you to:\n • Review my conversation history, especially the last 7M tokens spent.\n • Consider a token refund or credit for the failed attempts.\n • Let me know if there’s a better process I can follow to avoid this in\nthe future.\n\nThank you again for your time and for building something so\nforward-thinking. I’m hopeful this issue can be resolved, and that I can\nconfidently continue building with Rocket.\n\nWarm regards,\nDawood Hamdan",
                "relevance_score": 0.5390625,
                "metadata": {
                    "categories": [
                        "token_economy_credit_systems",
                        "integration_api_limitations"
                    ],
                    "from": "dawodhamdan.dh@gmail.com",
                    "response": "Hey David,\n\nSorry for the delayed response. Our team has thoroughly reviewed your\napplication logs and found that the issue is primarily related to the\nSupabase integration, which needs to be addressed first.\n\nWe’ll be applying some fixes from our end, which will be automatically\nupdated in your codebase and should help resolve the issue. Additionally,\nwe’ll share the necessary Supabase scripts to support the resolution.\n\nPlease allow us a day to prepare everything. In the meantime, if you have\nany requirement documents related to your application, feel free to share\nthem. This will help us guide you on the next steps more effectively.",
                    "subject": "Subject: Critical Token Usage Concern and Request for Review"
                }
            },
            {
                "query": "Hey All,\n\nI have charged my account with 5 million tokens on June 12.\n\nAnd since 12 June, I haven't used rocket for any screen generation, but my\ntokens balance is 0.\n\nCan you please explain where the 5 million tokens are?\n\nBest regards,\n\nᐧ",
                "relevance_score": 0.51171875,
                "metadata": {
                    "categories": [
                        "billing_financial_management"
                    ],
                    "from": "bishoy.yehya@gmail.com",
                    "response": "Hey Bishoy,\n\nKalpesh, this side. Thank you for reaching out. I checked your account and\nconfirmed that you purchased a refuel on June 12, 2025.\n\nHowever, your plan expired on June 24, 2025, so the tokens have lapsed.\nRefuel tokens can be carried forward for an active subscription, but since\nyour subscription was canceled, they don't show in your account.\n\nStill, I have added 5M tokens to your account so you can continue using\nRocket. I hope this helps; let me know if you have any other questions.",
                    "subject": "My Tokens Disappeared"
                }
            },
            {
                "query": "Hello,\nI tried to create an app on your website and realized that it's just\nanother unfinished product. Even with 2 million tokens, it failed to\ngenerate a working app. At first, it created something completely different\nthan what I asked for with 1 million tokens, and after a week I requested a\nfix — instead of providing a proper solution, it introduced at least three\nsyntax errors. When I clicked \"fix,\" it kept trying until the tokens ran\nout :)\nIn short, you're trying to sell a non-functional product — it's\nunfortunate, but that's the reality.\nGood thing I personally didn’t purchase it.\nJust another scam. I wonder how the international consumer rights office\nwill react to this?",
                "relevance_score": 0.48828125,
                "metadata": {
                    "categories": [
                        "token_economy_credit_systems"
                    ],
                    "from": "juzelt@gmail.com",
                    "response": "Hello Juozas,\n\nKalpesh this side. Thank you for reaching out, and I’m truly sorry for the\ninconvenience you’ve experienced. This is certainly not the experience we\naim to deliver.\n\nOur team has reviewed the issues in your app and made some fixes to our\ngeneration process, as there was a temporary issue on our end. These\nupdates have been automatically applied to your codebase and should resolve\nthe error you encountered. Please check your app and continue your work.\nYou should notice an improved experience now.\n\nLet us know if anything else comes up. We’re here to help!",
                    "subject": "skundas"
                }
            }
        ],
            "categories": ["billing_financial_management", "ai_performance_quality", "token_economy_credit_systems", "integration_api_limitations"],  # Ensure categories is always a list
            "attachments": [],  # Pass attachments from original query
        }
        generate_drafts_response = (
            await self.generate_drafts_usecase.generate_drafts(
                generate_drafts_query
            )
        )

        # Return the generate_drafts_response instead of search results
        return generate_drafts_response
