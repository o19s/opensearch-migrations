package com.northstar.search.web

import com.northstar.search.config.OpenSearchProperties
import com.northstar.search.search.AtlasSearchService
import org.springframework.web.bind.annotation.GetMapping
import org.springframework.web.bind.annotation.RequestMapping
import org.springframework.web.bind.annotation.RestController

@RestController
@RequestMapping("/api/admin")
class AdminController(
    private val atlasSearchService: AtlasSearchService,
    private val openSearchProperties: OpenSearchProperties
) {
    @GetMapping("/status")
    fun status(): Map<String, Any> {
        return mapOf(
            "app" to "northstar-enterprise-demo",
            "sampleDocumentCount" to atlasSearchService.sampleDocuments().size,
            "openSearchReachable" to atlasSearchService.openSearchReachable(),
            "targetOpenSearchUrl" to openSearchProperties.url,
            "targetIndexName" to openSearchProperties.indexName,
            "readAlias" to openSearchProperties.readAlias,
            "writeAlias" to openSearchProperties.writeAlias,
            "preferLiveSearch" to openSearchProperties.preferLiveSearch,
            "reindexScript" to "scripts/reindex_northstar.py",
            "dashboardsUrl" to "http://localhost:5601",
            "healthUrl" to "/actuator/health"
        )
    }
}
