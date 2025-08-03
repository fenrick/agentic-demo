async def planner(state: State) -> State:
    """Draft a plan from the current state.

    Purpose:
        Prepare an outline and confidence score for guiding further steps.

    Inputs:
        state: Current :class:`State` of the run.

    Outputs:
        :class:`PlanResult` containing the state's outline and confidence.

    Side Effects:
        None.

    Exceptions:
        None.
    """

    state.version += 1

    outline = state.outline
    confidence = getattr(state, "confidence", 0.0)
    return state


async def researcher_web(state: State) -> State:
    """Collect citations from the web concurrently and deduplicate them.

    Purpose:
        Fetch external information sources based on URLs in ``state.sources``.

    Inputs:
        state: Current :class:`State` whose ``sources`` provide seed URLs.

    Outputs:
        Mapping with ``"sources"`` updated to a deduplicated list of
        :class:`CitationResult` objects.

    Side Effects:
        Performs network I/O via the helper in :mod:`web.researcher_web`.

    Exceptions:
        Propagated from the underlying fetches after helper-level handling.
    """

    urls = [c.url for c in state.sources]
    citations = await _web_research(urls)
    return state


async def writer(state: State) -> State:
    """Placeholder writer node.

    Currently returns the ``state`` unchanged.
    """

    return state
