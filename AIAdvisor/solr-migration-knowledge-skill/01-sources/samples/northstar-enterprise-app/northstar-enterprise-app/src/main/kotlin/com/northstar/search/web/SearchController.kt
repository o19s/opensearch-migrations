package com.northstar.search.web

import com.northstar.search.domain.SearchRequest
import com.northstar.search.domain.SearchResponse
import com.northstar.search.search.AtlasSearchService
import org.springframework.web.bind.annotation.GetMapping
import org.springframework.web.bind.annotation.RequestMapping
import org.springframework.web.bind.annotation.RequestParam
import org.springframework.web.bind.annotation.RestController

@RestController
@RequestMapping("/api/search")
class SearchController(
    private val atlasSearchService: AtlasSearchService
) {
    @GetMapping
    fun search(
        @RequestParam(defaultValue = "") q: String,
        @RequestParam(required = false) region: String?,
        @RequestParam(required = false) docType: String?,
        @RequestParam(required = false) visibilityLevel: String?,
        @RequestParam(required = false) dealerTier: String?,
        @RequestParam(required = false) businessUnit: String?
    ): SearchResponse {
        return atlasSearchService.search(
            SearchRequest(
                query = q,
                region = region,
                docType = docType,
                visibilityLevel = visibilityLevel,
                dealerTier = dealerTier,
                businessUnit = businessUnit
            )
        )
    }
}
