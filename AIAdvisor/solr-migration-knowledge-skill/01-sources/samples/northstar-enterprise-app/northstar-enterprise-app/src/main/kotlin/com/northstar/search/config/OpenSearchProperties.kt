package com.northstar.search.config

import org.springframework.boot.context.properties.ConfigurationProperties

@ConfigurationProperties(prefix = "northstar.opensearch")
data class OpenSearchProperties(
    var url: String = "http://localhost:9200",
    var readAlias: String = "atlas-search-read",
    var writeAlias: String = "atlas-search-write",
    var indexName: String = "atlas-search-v1",
    var preferLiveSearch: Boolean = true
)
