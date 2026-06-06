def normalize_job(title, link, country, description, source):

    return {
        "title": title.strip() if title else "",
        "link": link.strip() if link else "",
        "country": country.strip() if country else "Unknown",
        "description": description.strip() if description else "",
        "source": source
    }
