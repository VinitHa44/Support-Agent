import json
from typing import Dict, List, Tuple

from system.src.app.prompts.generate_drafts_prompts import (
    GENERATE_DRAFTS_USER_PROMPT,
)


class GenerateDraftsHelper:
    def __init__(self):
        pass

    async def format_rocket_docs_response(
        self, rocket_docs_response: List[Dict]
    ) -> List[Dict]:
        formatted_rocket_docs_response = []
        if rocket_docs_response:
            element = {}
            for result in rocket_docs_response:
                element["url"] = result.get("metadata", {}).get("url", "")
                element["content"] = result.get("query", "")
                formatted_rocket_docs_response.append(element)
        return formatted_rocket_docs_response

    async def format_dataset_response(
        self, dataset_response: List[Dict]
    ) -> List[Dict]:
        formatted_dataset_response = []
        if dataset_response:
            element = {}
            for result in dataset_response:
                element["query"] = result.get("query", "")
                element["response"] = result.get("metadata", {}).get(
                    "response", ""
                )
                element["from"] = result.get("metadata", {}).get("from", "")
                element["subject"] = result.get("metadata", {}).get(
                    "subject", ""
                )
                formatted_dataset_response.append(element)
        return formatted_dataset_response

    async def format_pinecone_results(
        self, rocket_docs_response: List[Dict], dataset_response: List[Dict]
    ) -> Tuple[List[Dict], List[Dict]]:
        with open(
            "intermediate_outputs/3_pinecone_rocket_docs_response.json", "w"
        ) as f:
            json.dump(rocket_docs_response, f)
        with open(
            "intermediate_outputs/4_pinecone_dataset_response.json", "w"
        ) as f:
            json.dump(dataset_response, f)
        if rocket_docs_response:
            rocket_docs_response = await self.format_rocket_docs_response(
                rocket_docs_response
            )
        if dataset_response:
            dataset_response = await self.format_dataset_response(
                dataset_response
            )
        return rocket_docs_response, dataset_response

    def format_user_prompt(
        self,
        sender: str,
        subject: str,
        body: str,
        rocket_doc_results: List[Dict],
        dataset_search_results: List[Dict],
        categories: List[str],
    ) -> str:
        # Format rocket docs results
        rocket_docs_formatted = f"ROCKET DOCS:\n"
        for result in rocket_doc_results:
            rocket_docs_formatted += f"{json.dumps(result)}\n"

        # Format dataset search results
        dataset_formatted = f"DATASET:\n"
        for idx, result in enumerate(dataset_search_results, 1):
            dataset_formatted += f"example-{idx}\n"
            dataset_formatted += f"From: {result.get('from', '')}\n"
            dataset_formatted += f"Subject: {result.get('subject', '')}\n"
            dataset_formatted += f"Query: {result.get('query', '')}\n"
            dataset_formatted += f"Response: {result.get('response', '')}\n"

            # Add separator if not the last example
            if idx < len(dataset_search_results):
                dataset_formatted += "\n-----\n"

        with open("intermediate_outputs/5_rocket_docs_response.txt", "w") as f:
            f.write(rocket_docs_formatted)
        with open("intermediate_outputs/6_dataset_response.txt", "w") as f:
            f.write(dataset_formatted)

        with open("session-data/categories.json", "r") as f:
            categories_data = json.load(f)
        categories_data = categories_data.get("categories", {})

        formatted_categories = f"CATEGORIES:\n"
        filtered_categories_data = {}
        for category in categories:
            if category in categories_data:
                filtered_categories_data[category] = categories_data[category]

        formatted_categories += f"{json.dumps(filtered_categories_data)}\n"

        with open("intermediate_outputs/7_categories.txt", "w") as f:
            f.write(formatted_categories)

        user_prompt = GENERATE_DRAFTS_USER_PROMPT.format(
            docs_content=rocket_docs_formatted,
            email_content=f"From: {sender}\nSubject: {subject}\nBody: {body}",
            reference_templates=dataset_formatted,
            categories=formatted_categories,
        )

        return user_prompt
